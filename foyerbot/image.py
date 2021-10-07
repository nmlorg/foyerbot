"""Generate a difficult-to-read image representation of a short string."""

import captcha.image

CAPTCHA = captcha.image.ImageCaptcha(400, 100)


def render(text):
    """Generate a difficult-to-read image representation of a short string."""

    return CAPTCHA.generate(text)
