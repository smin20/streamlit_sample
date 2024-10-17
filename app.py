import streamlit as st

# Title and Header examples
st.title("Welcome to My Stock Analysis App")
st.header("Stock Data Overview")
st.subheader("Real-time Stock Updates")

# Markdown examples with various text formatting
st.markdown("# This is a Heading in Markdown")
st.markdown("## This is a Subheading in Markdown")
st.markdown("### Smaller Subheading Example")
# st.markdown("""
# **Bold Text Example**

# *Italic Text Example*

# ~~Strikethrough Example~~

# `Inline Code Example`

# > Blockquote Example
# """)

# Creating links and images with Markdown
st.markdown("[Streamlit Documentation](https://docs.streamlit.io/)")
# st.markdown("![Sample Image](https://via.placeholder.com/150)")

# Lists in Markdown
st.markdown("""
- Bullet list item 1
- Bullet list item 2
  - Sub-bullet item 1
  - Sub-bullet item 2
""")

st.markdown("""
1. Numbered list item 1
2. Numbered list item 2
   1. Sub-item 1
   2. Sub-item 2
""")

# Custom HTML in Markdown
st.markdown("""
<div style='background-color:lightblue; padding:10px; border-radius:5px'>
    This is a **custom block** with HTML and inline style.
</div>
""", unsafe_allow_html=True)

# # Highlighting code with Markdown
# st.markdown("""
# ```python
# # This is a code block in Python
# def my_function():
#     return "Hello, Streamlit!")
#     """