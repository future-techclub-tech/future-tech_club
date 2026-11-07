document.addEventListener("DOMContentLoaded", () => {
  document.querySelectorAll("[data-rich-editor]").forEach((editor) => {
    const field = editor.closest(".rich-text-field");
    const form = editor.closest("form");
    const source = field?.querySelector("[data-rich-source]");
    if (!field || !form || !source) return;
    let savedSelection = null;

    const saveSelection = () => {
      const selection = window.getSelection();
      if (selection?.rangeCount && editor.contains(selection.anchorNode)) {
        savedSelection = selection.getRangeAt(0).cloneRange();
      }
    };

    const restoreSelection = () => {
      editor.focus();
      if (!savedSelection) return;
      const selection = window.getSelection();
      selection.removeAllRanges();
      selection.addRange(savedSelection);
    };

    const clearFormatting = () => {
      restoreSelection();
      const selection = window.getSelection();
      let range = selection?.rangeCount ? selection.getRangeAt(0) : null;
      if (!range || !editor.contains(range.startContainer)) return;
      if (range.collapsed) {
        const anchor = range.startContainer.nodeType === Node.ELEMENT_NODE
          ? range.startContainer
          : range.startContainer.parentElement;
        const block = anchor?.closest("p,div,h2,h3,h4,li,blockquote,td,th")
          || editor;
        range = document.createRange();
        range.selectNodeContents(block);
      }

      const blocks = Array.from(editor.querySelectorAll(
        "p,div,h2,h3,h4,li,blockquote,td,th",
      )).filter((block) => range.intersectsNode(block));
      const fragment = range.extractContents();
      const removableTags = new Set([
        "A", "B", "CODE", "DEL", "EM", "FONT", "I", "S", "SPAN",
        "STRIKE", "STRONG", "SUB", "SUP", "U",
      ]);
      const cleanNode = (node) => {
        if (node.nodeType !== Node.ELEMENT_NODE) return;
        Array.from(node.children).forEach(cleanNode);
        if (removableTags.has(node.tagName)) {
          node.replaceWith(...node.childNodes);
          return;
        }
        node.removeAttribute("style");
      };
      Array.from(fragment.children).forEach(cleanNode);
      blocks.forEach((block) => {
        block.removeAttribute("style");
      });
      let ancestor = range.startContainer.nodeType === Node.ELEMENT_NODE
        ? range.startContainer
        : range.startContainer.parentElement;
      while (ancestor && ancestor !== editor) {
        const parent = ancestor.parentElement;
        if (removableTags.has(ancestor.tagName) && ancestor.parentNode) {
          const trailingRange = document.createRange();
          trailingRange.setStart(range.startContainer, range.startOffset);
          trailingRange.setEndAfter(ancestor);
          const trailingContent = trailingRange.extractContents();
          ancestor.parentNode.insertBefore(trailingContent, ancestor.nextSibling);
          range.setStartAfter(ancestor);
          range.collapse(true);
        }
        ancestor = parent;
      }
      range.insertNode(fragment);
      selection.removeAllRanges();
      selection.addRange(range);
      saveSelection();
    };

    editor.addEventListener("keyup", saveSelection);
    editor.addEventListener("mouseup", saveSelection);
    editor.addEventListener("input", saveSelection);
    document.addEventListener("selectionchange", saveSelection);

    field.querySelectorAll("[data-rich-command]").forEach((button) => {
      button.addEventListener("mousedown", (event) => event.preventDefault());
      button.addEventListener("click", () => {
        restoreSelection();
        document.execCommand(
          button.dataset.richCommand,
          false,
          button.dataset.richValue || null,
        );
      });
    });

    field.querySelectorAll("[data-rich-color]").forEach((input) => {
      input.addEventListener("pointerdown", saveSelection);
      input.addEventListener("focus", saveSelection);
      input.addEventListener("change", () => {
        restoreSelection();
        document.execCommand(input.dataset.richColor, false, input.value);
      });
    });

    field.querySelectorAll("[data-rich-action]").forEach((button) => {
      button.addEventListener("mousedown", (event) => event.preventDefault());
      button.addEventListener("click", () => {
        restoreSelection();
        if (button.dataset.richAction === "insertTable") {
          const rows = Number(field.querySelector("[data-rich-rows]")?.value);
          const columns = Number(field.querySelector("[data-rich-columns]")?.value);
          if (
            !Number.isInteger(rows)
            || !Number.isInteger(columns)
            || rows < 1
            || columns < 1
            || rows > 50
            || columns > 50
            || rows * columns > 1000
          ) {
            window.alert("Choose 1–50 rows and columns, with no more than 1,000 cells.");
            return;
          }
          const cells = Array.from({ length: rows }, () => (
            `<tr>${"<td><br></td>".repeat(columns)}</tr>`
          )).join("");
          document.execCommand(
            "insertHTML",
            false,
            `<table><tbody>${cells}</tbody></table><p><br></p>`,
          );
        } else if (button.dataset.richAction === "clearFormatting") {
          clearFormatting();
        } else if (button.dataset.richAction === "mergeCells") {
          const selection = window.getSelection();
          const range = selection?.rangeCount ? selection.getRangeAt(0) : null;
          if (!range || range.collapsed) {
            window.alert("Select text across adjacent table cells first.");
            return;
          }

          const selectedCells = Array.from(editor.querySelectorAll("td, th"))
            .filter((cell) => range.intersectsNode(cell));
          const table = selectedCells[0]?.closest("table");
          if (
            selectedCells.length < 2
            || !table
            || selectedCells.some((cell) => cell.closest("table") !== table)
          ) {
            window.alert("Select at least two adjacent cells in the same table.");
            return;
          }

          const rows = Array.from(table.rows).filter(
            (row) => row.closest("table") === table,
          );
          const grid = [];
          const cellPositions = new Map();
          rows.forEach((row, rowIndex) => {
            grid[rowIndex] ||= [];
            let columnIndex = 0;
            Array.from(row.cells).forEach((cell) => {
              while (grid[rowIndex][columnIndex]) columnIndex += 1;
              const rowSpan = Math.max(1, cell.rowSpan || 1);
              const columnSpan = Math.max(1, cell.colSpan || 1);
              cellPositions.set(cell, {
                top: rowIndex,
                left: columnIndex,
                bottom: rowIndex + rowSpan - 1,
                right: columnIndex + columnSpan - 1,
              });
              for (let r = rowIndex; r < rowIndex + rowSpan; r += 1) {
                grid[r] ||= [];
                for (let c = columnIndex; c < columnIndex + columnSpan; c += 1) {
                  grid[r][c] = cell;
                }
              }
              columnIndex += columnSpan;
            });
          });

          const selected = new Set(selectedCells);
          const positions = selectedCells.map((cell) => cellPositions.get(cell));
          const top = Math.min(...positions.map((position) => position.top));
          const left = Math.min(...positions.map((position) => position.left));
          const bottom = Math.max(...positions.map((position) => position.bottom));
          const right = Math.max(...positions.map((position) => position.right));
          const rectangular = selectedCells.every((cell) => {
            const position = cellPositions.get(cell);
            return position.top >= top
              && position.left >= left
              && position.bottom <= bottom
              && position.right <= right;
          }) && Array.from({ length: bottom - top + 1 }, (_, rowOffset) => (
            Array.from({ length: right - left + 1 }, (_, columnOffset) => (
              selected.has(grid[top + rowOffset]?.[left + columnOffset])
            )).every(Boolean)
          )).every(Boolean);

          if (!rectangular) {
            window.alert("Select a complete rectangular block of adjacent cells.");
            return;
          }

          const firstCell = grid[top][left];
          const orderedCells = selectedCells.slice().sort((a, b) => {
            const aPosition = cellPositions.get(a);
            const bPosition = cellPositions.get(b);
            return aPosition.top - bPosition.top || aPosition.left - bPosition.left;
          });
          const content = orderedCells
            .map((cell) => cell.innerHTML)
            .filter((html) => html && html !== "<br>")
            .join("<br>");
          firstCell.innerHTML = content || "<br>";
          firstCell.rowSpan = bottom - top + 1;
          firstCell.colSpan = right - left + 1;
          orderedCells.filter((cell) => cell !== firstCell).forEach((cell) => cell.remove());
        } else if (button.dataset.richAction === "insertLink") {
          const value = window.prompt("Enter a web address or email link:");
          if (!value) return;
          const href = value.trim();
          if (
            !href
            || href.startsWith("//")
            || href.includes("\\")
            || /^(?:javascript|data|vbscript):/i.test(href)
          ) {
            window.alert("Enter a safe web address, email link, or relative link.");
            return;
          }
          document.execCommand("createLink", false, href);
        }
      });
    });

    form.addEventListener("submit", () => {
      source.value = editor.innerHTML;
    });
  });
});
