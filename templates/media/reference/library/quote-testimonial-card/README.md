# quote-testimonial-card

Pull quote / testimonial card with opening mark, attributed quote, and optional role.

- **Canonical ID:** `quote-testimonial-card`
- **Runtime kind:** `quote_testimonial` (native injector)
- **Injector:** `shared/pptx/pattern_injectors/quote_testimonial.py`
- **Status:** Native injector registered. SVG reference assets may be added later.

## Parameters
- `quote` (str): The quotation text (required)
- `attribution` (str, optional): Who said it
- `role` (str, optional): Title/role of the person
- `accent_color` (str, optional): Token for accent line (default: `primary`)
- `show_accent_line` (bool, optional): Display left accent line (default: True)
