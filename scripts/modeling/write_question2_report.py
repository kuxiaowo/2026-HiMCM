"""Compatibility entry point: regenerate Q2 formal chapter and original figures.

The previous concise generator is historical source text in archive/.
This entry point no longer overwrites the formal manuscript with that draft.
"""
from verify_question2 import main as verify_results
from build_question2_paper_figures import main as draw_figures
from write_question2_chapter import main as write_chapter


def main():
    verify_results()
    draw_figures()
    write_chapter()


if __name__ == '__main__':
    main()
