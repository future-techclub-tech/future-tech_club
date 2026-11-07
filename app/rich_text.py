from html import escape
from html.parser import HTMLParser
from markupsafe import Markup
import re
from urllib.parse import urlsplit


class _RichTextSanitizer(HTMLParser):
    allowed_tags = {
        "a", "b", "blockquote", "br", "caption", "code", "col", "colgroup",
        "div", "em", "font", "h2", "h3", "h4", "i", "li", "ol", "p", "pre",
        "s", "span", "strong", "sub", "sup", "table", "tbody", "td", "tfoot",
        "th", "thead", "tr", "u", "ul",
    }
    void_tags = {"br", "col"}
    blocked_tags = {"script", "style"}
    font_sizes = {
        "1": "8pt",
        "2": "10pt",
        "3": "12pt",
        "4": "14pt",
        "5": "18pt",
        "6": "24pt",
        "7": "36pt",
    }

    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.output = []
        self.open_tags = []
        self.blocked_depth = 0

    @staticmethod
    def safe_color(value):
        value = value.strip().lower()
        if re.fullmatch(r"#[0-9a-f]{3,8}", value):
            return value
        if re.fullmatch(
            r"rgba?\(\s*\d{1,3}\s*,\s*\d{1,3}\s*,\s*\d{1,3}"
            r"(?:\s*,\s*(?:0|1|0?\.\d+))?\s*\)",
            value,
        ):
            return value
        if value in {"black", "blue", "gray", "green", "orange", "purple", "red", "white", "yellow"}:
            return value
        return ""

    @classmethod
    def safe_style(cls, value):
        safe_declarations = []
        for declaration in value.split(";"):
            property_name, separator, property_value = declaration.partition(":")
            if not separator:
                continue
            property_name = property_name.strip().lower()
            property_value = property_value.strip().lower()
            if property_name in {"color", "background-color"}:
                safe_value = cls.safe_color(property_value)
            elif property_name == "font-size" and re.fullmatch(
                r"(?:[1-9]\d?|1\d\d)(?:\.\d{1,2})?(?:px|pt|em|rem|%)",
                property_value,
            ):
                safe_value = property_value
            elif property_name == "text-align" and property_value in {
                "left", "center", "right", "justify",
            }:
                safe_value = property_value
            else:
                continue
            if safe_value:
                safe_declarations.append(f"{property_name}: {safe_value}")
        return "; ".join(safe_declarations)

    @staticmethod
    def safe_href(value):
        value = value.strip()
        if not value or "\\" in value or any(ord(char) < 32 for char in value):
            return ""
        try:
            parsed = urlsplit(value)
        except ValueError:
            return ""
        scheme = parsed.scheme.lower()
        if scheme in {"http", "https"} and parsed.netloc:
            return value
        if scheme == "mailto" and parsed.path:
            return value
        if not scheme and not value.startswith("//"):
            return value
        return ""

    def attributes_for(self, tag, attrs):
        safe_attrs = []
        if tag == "a":
            href = self.safe_href(dict(attrs).get("href", ""))
            if href:
                safe_attrs.append(f' href="{escape(href, quote=True)}"')

        styles = []
        for name, value in attrs:
            if name == "style" and value:
                safe_style = self.safe_style(value)
                if safe_style:
                    styles.append(safe_style)
        if tag == "font":
            attr_values = dict(attrs)
            color = self.safe_color(attr_values.get("color", ""))
            if color:
                styles.append(f"color: {color}")
            font_size = self.font_sizes.get(attr_values.get("size", ""))
            if font_size:
                styles.append(f"font-size: {font_size}")
        if styles:
            safe_attrs.append(f' style="{escape("; ".join(styles), quote=True)}"')

        if tag in {"td", "th", "col"}:
            for name, value in attrs:
                if name in {"colspan", "rowspan"} and value and value.isdigit():
                    if 1 <= int(value) <= 50:
                        safe_attrs.append(f' {name}="{value}"')
        return "".join(safe_attrs)

    @staticmethod
    def normalized_tag(tag):
        return "span" if tag == "font" else tag

    def handle_starttag(self, tag, attrs):
        tag = tag.lower()
        if self.blocked_depth:
            if tag in self.blocked_tags:
                self.blocked_depth += 1
            return
        if tag in self.blocked_tags:
            self.blocked_depth = 1
        elif tag in self.allowed_tags:
            normalized_tag = self.normalized_tag(tag)
            self.output.append(
                f"<{normalized_tag}{self.attributes_for(tag, attrs)}>"
            )
            if tag not in self.void_tags:
                self.open_tags.append((tag, normalized_tag))

    def handle_startendtag(self, tag, attrs):
        tag = tag.lower()
        if not self.blocked_depth and tag in self.allowed_tags:
            normalized_tag = self.normalized_tag(tag)
            self.output.append(
                f"<{normalized_tag}{self.attributes_for(tag, attrs)}>"
            )
            if tag not in self.void_tags:
                self.output.append(f"</{normalized_tag}>")

    def handle_endtag(self, tag):
        tag = tag.lower()
        if self.blocked_depth:
            if tag in self.blocked_tags:
                self.blocked_depth -= 1
            return
        normalized_tag = self.normalized_tag(tag)
        if any(open_tag == tag for open_tag, _ in self.open_tags):
            while self.open_tags:
                _, normalized_open_tag = self.open_tags.pop()
                self.output.append(f"</{normalized_open_tag}>")
                if normalized_open_tag == normalized_tag:
                    break

    def handle_data(self, data):
        if not self.blocked_depth:
            self.output.append(escape(data, quote=False).replace("\n", "<br>"))


def sanitize_rich_text(value):
    parser = _RichTextSanitizer()
    parser.feed(value or "")
    parser.close()
    while parser.open_tags:
        _, normalized_tag = parser.open_tags.pop()
        parser.output.append(f"</{normalized_tag}>")
    return Markup("".join(parser.output))
