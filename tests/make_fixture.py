"""Build a synthetic two-column, BMC-style test paper (needs reportlab).

Layout quirks it reproduces on purpose:
- full-width title + structured abstract on page 1
- two-column body text
- a chart drawn with VECTOR objects only (no embedded image) + "Figure 1." caption
- Conclusions placed BEFORE Methods, followed by a long multi-page reference list
"""
import sys
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas

W, H = A4
LOREM = ("Octopods rely on haemocyanin to transport oxygen in cold water and the "
         "pigment binds oxygen more tightly as temperature falls. ")


def column_text(c, x, y, lines, width_chars=48, leading=12):
    for line in lines:
        c.drawString(x, y, line[:width_chars])
        y -= leading
    return y


def wrap(text, n=48):
    words, out, cur = text.split(), [], ""
    for w in words:
        if len(cur) + len(w) + 1 > n:
            out.append(cur)
            cur = w
        else:
            cur = (cur + " " + w).strip()
    if cur:
        out.append(cur)
    return out


def build(path):
    c = canvas.Canvas(path, pagesize=A4)
    c.setFont("Helvetica-Bold", 16)
    c.drawString(50, H - 60, "Blue blood on ice: a synthetic test paper about octopus haemocyanin")
    c.setFont("Helvetica", 10)
    c.drawString(50, H - 78, "Test Author A, Test Author B, Test Author C, Department of Zoology, Example University")
    y = H - 105
    for line in ["Abstract", "Introduction", "The Antarctic Ocean hosts a rich fauna near freezing temperatures across the whole year.",
                 "Results", "At 0 C the haemocyanin released only a small fraction of its bound oxygen in the model.",
                 "Conclusions", "Higher pigment concentrations compensate for poor oxygen unloading in the cold.",
                 "Keywords: Cephalopod, Haemocyanin, Oxygen affinity"]:
        c.drawString(50, y, line)
        y -= 13
    top = y - 15
    left = [*wrap("Introduction"), *wrap(LOREM * 6), "", "Results", *wrap(LOREM * 4)]
    right = [*wrap(LOREM * 5), "", "Discussion", *wrap(LOREM * 6)]
    column_text(c, 50, top, left)
    column_text(c, W / 2 + 10, top, right)
    c.showPage()

    # Page 2: vector-only chart + caption, two columns of text below it
    c.setFont("Helvetica", 9)
    c.rect(60, H - 330, 470, 250)
    import math
    for i in range(40):  # 40 small vector bars and markers
        x = 70 + i * 11
        hgt = 20 + 80 * (1 + math.sin(i / 4))
        c.rect(x, H - 320, 6, hgt, fill=1)
        c.circle(x + 3, H - 320 + hgt + 6, 2)
    c.drawString(60, H - 350, "Figure 1. Oxygen released by haemocyanin at 0 C and 10 C (mean +/- 95% CI, n = 6).")
    y = column_text(c, 50, H - 380, wrap(LOREM * 8))
    y2 = column_text(c, W / 2 + 10, H - 380, ["Conclusions", *wrap("This study shows haemocyanin is important for cold tolerance in octopods and that thicker blood is the cost of carrying more pigment.")])
    column_text(c, W / 2 + 10, y2 - 12, ["Methods", *wrap("Animals were sampled by bottom trawl and haemolymph was analysed in a diffusion chamber. " * 3)])
    c.showPage()

    # Pages 3-6: long reference list (mentions 'Conclusions' and 'Summary' inside titles)
    c.setFont("Helvetica", 9)
    c.drawString(50, H - 50, "References")
    n = 1
    for page in range(4):
        y = H - 70
        while y > 60:
            c.drawString(50, y, f"{n}. Smith J et al. Conclusions about fish blood and a Summary of results. J Test Biol. {1990 + n % 30}.")
            y -= 12
            n += 1
        c.showPage()
    c.save()


if __name__ == "__main__":
    build(sys.argv[1] if len(sys.argv) > 1 else "fixture.pdf")
