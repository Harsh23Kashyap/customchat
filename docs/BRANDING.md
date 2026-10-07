# Brand from logo

In Configuration > Wording, upload a PNG, JPG, WebP or GIF (up to4MB). Existing background removal and edge softness stay optional. Choose **Build colors from logo** to derive both light and dark palettes in the preview, then Save look. Colors remain editable in Colors; generating again replaces both palettes. A monochrome/empty image uses the default green when no usable non-background pixels exist.

Palette extraction runs in the browser. No image is sent to a model or third-party service. The saved processed logo stays in the local theme file, becomes the browser favicon and can appear as an optional4%-opacity watermark behind the reading area. Remove the logo to remove its favicon/watermark. The palette itself is kept, so removing a logo does not discard manual color work.

Generated main/soft/brand/accent/error text colors are checked against all five generated background surfaces at4.5:1. This is not a whole-UI accessibility certification: manual color overrides, user background images, uploaded artwork and existing disabled-state styles can change contrast. Review both modes in the live preview.

Validation:132 Python tests;400generated text/surface contrast pairs over8seed colors in both modes; transparent/white fallback; actual browser upload, derive, save, PNG favicon200, watermark, light/dark pixel inspection, zero browser errors. No paid model calls, deployment or publication.
