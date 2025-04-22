from html_parse import extract_clean_text


print(
    extract_clean_text("""
    <body>
                          <p class="right">– <i>J. B. S. Haldane</i></p>
                          </body>
                         """)
)
