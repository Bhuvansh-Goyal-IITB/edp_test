import os
import shutil
from html_parse import extract_epub_text
from bdf_parse import BDF_Font, Text_Justification, Line_Break_Algorithm
from PIL import Image

# epub_path = "./book.epub"
# text = extract_epub_text(epub_path)
#
# page_indices = [0]
#
# margin = (30, 30)
#
# font_path = "./font.bdf"
# font = BDF_Font(font_path)
#
# x, y = margin[0], margin[1] + font.ascent
#
# img_width, img_height = 480, 648
#
# word_buffer = ""
# word_start_index = 0
#
# for i, char in enumerate(text):
#     if char == " " or char == "\n" or char == "\f":
#         if len(word_buffer) > 0:
#             width = font.get_width(word_buffer)
#
#             if x + width + margin[0] >= img_width:
#                 x = margin[0] + width
#                 y += font.ascent + font.descent - 1
#             else:
#                 x += width
#
#             if y + font.descent + margin[1] >= img_height:
#                 x = margin[0] + width
#                 y = margin[1] + font.ascent - 1
#                 page_indices.append(word_start_index)
#
#         if char == " ":
#             space_glyph = font.get_glyph(32)
#
#             if space_glyph is not None:
#                 x += space_glyph.x_advance
#
#         if char == "\n":
#             x = margin[0]
#             y += font.ascent + font.descent - 1
#
#         if char == "\f":
#             x = margin[0]
#             y = img_height
#
#         word_buffer = ""
#     else:
#         if len(word_buffer) == 0:
#             word_start_index = i
#         word_buffer += char
#
# for i in range(1, len(page_indices) + 1):
#     page_text = ""
#     if i == len(page_indices):
#         page_text = text[page_indices[i - 1] :]
#     else:
#         page_text = text[page_indices[i - 1] : page_indices[i]]
#
#     img = Image.new("1", (img_width, img_height), 1)
#     font.render_text(img, page_text, margin)
#
#     img.save(f"./book_render/{i}.png")


def render_page(
    text,
    line_indices,
    page_number,
    font: BDF_Font,
    img_size,
    margin,
    text_justification,
    output_folder="book_render",
):
    img = Image.new("1", img_size, 1)
    font.render_line_indices(line_indices, img, text, margin, text_justification)

    if page_number == 1:
        if os.path.exists(output_folder):
            shutil.rmtree(output_folder)

        os.makedirs(output_folder)

    img.save(f"{output_folder}/{page_number}.png")


def render_book(
    epub_path,
    font_path,
    img_size=(480, 648),
    margin=(20, 20),
    line_break_algorithm=Line_Break_Algorithm.OPTIMAL,
    text_justification=Text_Justification.FULL,
):
    book_text = extract_epub_text(epub_path)
    font = BDF_Font(font_path)

    page_number = 0

    max_lines = 0
    y = margin[1] + font.ascent - 1

    while y + font.descent + margin[0] < img_size[1]:
        y += font.ascent + font.descent - 1
        max_lines += 1

    page_line_indices = []
    text_block_buffer = ""
    text_block_buffer_start_index = 0

    for i, char in enumerate(book_text):
        if char != "\n" and char != "\f":
            if len(text_block_buffer) == 0:
                text_block_buffer_start_index = i
            text_block_buffer += char
        else:
            # print(text_block_buffer)
            if len(text_block_buffer) > 0:
                text_block_line_indices = []

                if line_break_algorithm == Line_Break_Algorithm.OPTIMAL:
                    text_block_line_indices = font.optimal_line_indices(
                        text_block_buffer, img_size[0] - (2 * margin[0])
                    )
                else:
                    text_block_line_indices = font.greedy_line_indices(
                        text_block_buffer, img_size[0] - (2 * margin[0])
                    )

                text_block_line_indices = [
                    (
                        index[0] + text_block_buffer_start_index,
                        index[1] + text_block_buffer_start_index,
                    )
                    for index in text_block_line_indices
                ]

                for line_index in text_block_line_indices:
                    if len(page_line_indices) == max_lines:
                        page_number += 1
                        render_page(
                            book_text,
                            page_line_indices,
                            page_number,
                            font,
                            img_size,
                            margin,
                            text_justification,
                        )
                        print(f"page number {page_number}")
                        page_line_indices = [line_index]
                    else:
                        page_line_indices.append(line_index)

            if char == "\n":
                if len(page_line_indices) == max_lines:
                    page_number += 1
                    render_page(
                        book_text,
                        page_line_indices,
                        page_number,
                        font,
                        img_size,
                        margin,
                        text_justification,
                    )
                    print(f"page number {page_number}")
                    page_line_indices = []
                else:
                    page_line_indices.append((i, i))

            if char == "\f":
                page_number += 1
                render_page(
                    book_text,
                    page_line_indices,
                    page_number,
                    font,
                    img_size,
                    margin,
                    text_justification,
                )
                print(f"page number {page_number}")
                page_line_indices = []

            text_block_buffer = ""


epub_path = "./book.epub"
font_path = "./font.bdf"

render_book(
    epub_path,
    font_path,
    margin=(24, 24),
    line_break_algorithm=Line_Break_Algorithm.OPTIMAL,
    text_justification=Text_Justification.LEFT,
)
