import zipfile
import xml.etree.ElementTree as ET
from bs4 import BeautifulSoup, NavigableString, Tag
import os


def get_opf_path(container_xml):
    tree = ET.fromstring(container_xml)
    rootfile = tree.find(".//{urn:oasis:names:tc:opendocument:xmlns:container}rootfile")
    return rootfile.attrib["full-path"]


def extract_spine_and_manifest(opf_xml):
    ns = {"opf": "http://www.idpf.org/2007/opf"}
    tree = ET.fromstring(opf_xml)

    manifest = {
        item.attrib["id"]: item.attrib["href"]
        for item in tree.findall(".//opf:manifest/opf:item", ns)
    }

    spine_ids = [
        item.attrib["idref"] for item in tree.findall(".//opf:spine/opf:itemref", ns)
    ]
    return [manifest[i] for i in spine_ids if i in manifest]


def extract_clean_text(html_string):
    soup = BeautifulSoup(html_string, "html.parser", from_encoding="utf-8")
    tags_to_extract = {"p", "div", "h1", "h2", "h3", "h4", "h5", "h6"}

    text_parts = []

    def walk(node):
        if isinstance(node, NavigableString):
            # text = str(node)
            text = str(node).strip("\n")
            if text.strip():  # Preserve whitespace but skip pure-empty strings
                text_parts.append(text)
        elif isinstance(node, Tag):
            if node.name in tags_to_extract:
                if not any(
                    child.name in tags_to_extract
                    for child in node.find_all(recursive=False)
                ):
                    text = node.get_text().strip("\n")
                    if text.strip():
                        text_parts.append(text)
                    return  # Avoid walking into nested matching tags
            for child in node.contents:
                walk(child)

    walk(soup.body if soup.body else soup)

    return "\n".join(text_parts)


def extract_epub_text(epub_path):
    with zipfile.ZipFile(epub_path, "r") as z:
        # Step 1: find OPF path
        container_xml = z.read("META-INF/container.xml")
        opf_path = get_opf_path(container_xml)

        # Step 2: parse OPF to get ordered content files
        opf_dir = os.path.dirname(opf_path)
        opf_xml = z.read(opf_path)
        content_files = extract_spine_and_manifest(opf_xml)

        # Step 3: extract and process HTML content
        texts = []
        for file in content_files:
            full_path = os.path.join(opf_dir, file).replace("\\", "/")
            try:
                html = z.read(full_path)
                text = extract_clean_text(html)
                texts.append(text.strip())
            except KeyError:
                continue  # skip missing files

        texts = [text for text in texts if text != ""]
        return "\f".join(texts)


if __name__ == "__main__":
    epub_path = "./catcher_in_the_rye.epub"
    output_path = "extracted_text.txt"

    text = extract_epub_text(epub_path)
    with open(output_path, "w", encoding="utf-8") as f:
        f.write(text)
