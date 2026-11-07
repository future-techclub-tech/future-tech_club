(() => {
  const searchGroups = [...document.querySelectorAll("[data-user-search]")];
  searchGroups.forEach((search) => {
    const form = search.closest("form");
    const results = form.querySelector("[data-user-results]");
    const selectedContainer = form.querySelector("[data-user-selected]");
    const selectionCount = form.querySelector("[data-user-selection-count]");
    const selected = new Map();
    const teamSelect = form.querySelector("[data-project-team]");
    let requestNumber = 0;
    let searchTimer;

    const showMessage = (message) => {
      results.replaceChildren();
      const notice = document.createElement("p");
      notice.className = "task-user-empty";
      notice.textContent = message;
      results.append(notice);
      results.hidden = false;
    };

    const renderSelection = () => {
      selectedContainer.replaceChildren();
      selectionCount.textContent = String(selected.size);
      selected.forEach((user) => {
        const chip = document.createElement("span");
        chip.className = "task-user-chip";
        const label = document.createElement("span");
        label.textContent = `${user.display_name} · ${user.username} · ${user.role}`;
        const remove = document.createElement("button");
        remove.type = "button";
        remove.className = "task-user-remove";
        remove.textContent = "Remove";
        remove.setAttribute("aria-label", `Remove ${user.display_name}`);
        remove.addEventListener("click", () => {
          selected.delete(String(user.id));
          renderSelection();
          search.dispatchEvent(new Event("input"));
        });
        const hiddenInput = document.createElement("input");
        hiddenInput.type = "hidden";
        hiddenInput.name = "assignee_ids";
        hiddenInput.value = String(user.id);
        chip.append(label, remove, hiddenInput);
        selectedContainer.append(chip);
      });
    };

    const updateResults = async () => {
      const currentRequest = ++requestNumber;
      const query = search.value.trim();
      if (query.length < 2) {
        results.replaceChildren();
        results.hidden = true;
        return;
      }
      if (teamSelect && !teamSelect.value) {
        results.replaceChildren();
        results.hidden = true;
        return;
      }

      showMessage("Searching active accounts…");
      const params = new URLSearchParams({
        q: query,
        scope: search.dataset.scope,
      });
      if (teamSelect) params.set("team_id", teamSelect.value);
      try {
        const response = await fetch(`/tasks/search-users?${params}`, {
          headers: { Accept: "application/json" },
        });
        if (!response.ok) throw new Error("User search failed.");
        const payload = await response.json();
        if (currentRequest !== requestNumber) return;
        const users = payload.users.filter((user) => !selected.has(String(user.id)));
        if (!users.length) {
          showMessage("No matching active accounts found.");
          return;
        }
        results.replaceChildren();
        users.forEach((user) => {
          const option = document.createElement("button");
          option.type = "button";
          option.className = "task-user-result";
          option.textContent = `${user.display_name} · ${user.username} · ${user.role}`;
          option.addEventListener("click", () => {
            selected.set(String(user.id), user);
            renderSelection();
            updateResults();
          });
          results.append(option);
        });
        if (payload.has_more) {
          const refineHint = document.createElement("p");
          refineHint.className = "task-user-empty";
          refineHint.textContent = "Showing the first 20 matches. Add more letters to narrow your search.";
          results.append(refineHint);
        }
      } catch (error) {
        if (currentRequest === requestNumber) {
          showMessage("Could not search accounts. Please try again.");
          console.error(error);
        }
      }
    };

    search.addEventListener("input", () => {
      window.clearTimeout(searchTimer);
      searchTimer = window.setTimeout(updateResults, 250);
    });
    if (teamSelect) {
      teamSelect.addEventListener("change", () => {
        selected.clear();
        renderSelection();
        search.value = "";
        requestNumber += 1;
        updateResults();
      });
    }
    renderSelection();
    updateResults();
  });

  const form = document.querySelector("[data-project-task-form]");
  if (!form) return;

  const teamSelect = form.querySelector("[data-project-team]");
  const roleOptions = [...form.querySelectorAll("[data-project-role-choice]")];
  const refreshOptions = () => {
    const teamId = teamSelect.value;
    roleOptions.forEach((option) => {
      const visible = Boolean(teamId);
      option.hidden = !visible;
      if (!visible) option.querySelector("input").checked = false;
    });
  };

  teamSelect.addEventListener("change", refreshOptions);
  refreshOptions();
})();
