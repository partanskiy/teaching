// Two identical A5 handouts on one landscape A4 sheet.
// Keep every task in a single column within its own A5 half.

#let problem(number, source, url, body) = block(
  breakable: false,
  above: 8pt,
  below: 0pt,
)[
  #text(weight: "bold")[Задача #number]
  #text(size: 0.9em, style: "italic")[#link(url)[(#source)]]
  #linebreak()
  #body
]

#let handout(
  course: "Олимпиадная математика. 10 класс",
  title: "",
  date: "",
  text-size: 10.5pt,
  body,
) = {
  set document(title: course + ". " + title)
  set page(width: 297mm, height: 210mm, margin: 0mm)
  set text(font: "Times New Roman", size: text-size, lang: "ru")
  set par(justify: true, leading: 0.35em, spacing: 0pt)

  let half-width = 148.5mm
  let inset-x = 8mm
  let inset-y = 7mm
  let content-width = half-width - 2 * inset-x
  let content-height = 210mm - 2 * inset-y
  let half = [
    #align(right, text(size: 9pt, date))
    #v(1mm)
    #align(center, text(size: 12pt, weight: "bold", course))
    #v(1mm)
    #align(center, text(size: 11pt, weight: "bold", title))
    #v(1.5mm)
    #body
  ]

  context {
    let required = measure(block(width: content-width, half)).height
    assert(
      required <= content-height,
      message: "The handout needs " + repr(required) + " of height; A5 allows "
        + repr(content-height) + ". Adjust spacing or text-size.",
    )
    let panel() = block(
      width: half-width,
      height: 210mm,
      inset: (x: inset-x, y: inset-y),
      breakable: false,
      above: 0pt,
      below: 0pt,
      half,
    )
    place(
      top + left,
      dx: half-width,
      dy: inset-y,
      line(
        start: (0pt, 0pt),
        end: (0pt, content-height),
        stroke: (paint: luma(65%), thickness: 0.45pt, dash: "dashed"),
      ),
    )
    grid(columns: (half-width, half-width), gutter: 0pt, panel(), panel())
  }
}
