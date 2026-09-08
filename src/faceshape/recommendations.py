"""
recommendations.py — Style Recommendation Engine with Visual Assets
"""


def _h(gender, slug):
    return f"/static/rec/{gender}/hairstyle/{slug}.png"


def _g(slug):
    return f"/static/rec/glasses/{slug}.png"


RECOMMENDATIONS = {
    "male": {
        "Heart": {
            "hairstyle": [
                {
                    "name": "Side-Swept Undercut",
                    "desc": "Adds width to lower face",
                    "image": _h("male", "undercut"),
                },
                {
                    "name": "Textured Quiff",
                    "desc": "Balances the narrow chin",
                    "image": _h("male", "quiff"),
                },
                {
                    "name": "Medium Waves",
                    "desc": "Softens a wide forehead",
                    "image": _h("male", "medium-waves"),
                },
                {
                    "name": "High Fade",
                    "desc": "Clean and modern look",
                    "image": _h("male", "high-fade"),
                },
            ],
            "glasses": [
                {"name": "Aviator", "desc": "Complements wide forehead", "image": _g("aviator")},
                {
                    "name": "Round Frames",
                    "desc": "Balances sharp chin",
                    "image": _g("round-frames"),
                },
                {
                    "name": "Oval Frames",
                    "desc": "Softens overall structure",
                    "image": _g("oval-frames"),
                },
            ],
            "specific": [
                {"name": "Full Beard", "desc": "Widens the chin significantly"},
                {"name": "Goatee", "desc": "Adds length to chin"},
                {"name": "Short Boxed Beard", "desc": "Creates jaw definition"},
            ],
            "specific_label": "Beard Style",
            "tip": (
                "Focus on adding width around your jaw and chin. Avoid styles that add volume "
                "to the top of your head."
            ),
        },
        "Oblong": {
            "hairstyle": [
                {
                    "name": "Textured Crop",
                    "desc": "Adds width, reduces length",
                    "image": _h("male", "textured-crop"),
                },
                {
                    "name": "Side Part",
                    "desc": "Volume on sides, modern look",
                    "image": _h("male", "side-part"),
                },
                {
                    "name": "Curly Medium",
                    "desc": "Widens face appearance",
                    "image": _h("male", "curly-medium"),
                },
                {
                    "name": "Medium Waves",
                    "desc": "Natural width and softness",
                    "image": _h("male", "medium-waves"),
                },
            ],
            "glasses": [
                {"name": "Wayfarer", "desc": "Balances the long face", "image": _g("wayfarer")},
                {
                    "name": "Square Frames",
                    "desc": "Wide frames add balance",
                    "image": _g("square-frames"),
                },
                {
                    "name": "Rectangular",
                    "desc": "Bold horizontal statement",
                    "image": _g("rectangular"),
                },
            ],
            "specific": [
                {"name": "Full Bushy Beard", "desc": "Adds width to the jaw"},
                {"name": "Wide Mutton Chops", "desc": "Balances face length"},
                {"name": "Full Sides Trim", "desc": "Full on sides, trim chin"},
            ],
            "specific_label": "Beard Style",
            "tip": (
                "Avoid tall hairstyles that add height. Go for styles with width on the sides "
                "to balance proportions."
            ),
        },
        "Oval": {
            "hairstyle": [
                {
                    "name": "Classic Pompadour",
                    "desc": "Works great with oval face",
                    "image": _h("male", "pompadour"),
                },
                {
                    "name": "Textured Undercut",
                    "desc": "Modern and versatile",
                    "image": _h("male", "undercut"),
                },
                {
                    "name": "Slicked Back",
                    "desc": "Clean professional look",
                    "image": _h("male", "slicked-back"),
                },
                {
                    "name": "Crew Cut",
                    "desc": "Timeless and flattering",
                    "image": _h("male", "crew-cut"),
                },
            ],
            "glasses": [
                {"name": "Wayfarer", "desc": "Timeless classic choice", "image": _g("wayfarer")},
                {"name": "Rectangular", "desc": "Professional look", "image": _g("rectangular")},
                {"name": "Round Frames", "desc": "Trendy and stylish", "image": _g("round-frames")},
            ],
            "specific": [
                {"name": "Full Beard", "desc": "Classic masculine look"},
                {"name": "Short Stubble", "desc": "Clean and modern"},
                {"name": "Clean Shaven", "desc": "Sharp and polished"},
            ],
            "specific_label": "Beard Style",
            "tip": (
                "Oval is the most versatile face shape — most hairstyles and beard styles will "
                "suit you well."
            ),
        },
        "Round": {
            "hairstyle": [
                {
                    "name": "High Fade",
                    "desc": "Elongates the face",
                    "image": _h("male", "high-fade"),
                },
                {
                    "name": "Quiff",
                    "desc": "Adds height and definition",
                    "image": _h("male", "quiff"),
                },
                {
                    "name": "Pompadour",
                    "desc": "Classic height and volume",
                    "image": _h("male", "pompadour"),
                },
                {
                    "name": "Slicked Back",
                    "desc": "Slimming and modern",
                    "image": _h("male", "slicked-back"),
                },
            ],
            "glasses": [
                {
                    "name": "Rectangular",
                    "desc": "Adds definition and angles",
                    "image": _g("rectangular"),
                },
                {
                    "name": "Angular Rect",
                    "desc": "Contrasts soft curves",
                    "image": _g("angular-rect"),
                },
                {
                    "name": "Square Frames",
                    "desc": "Strong angular contrast",
                    "image": _g("square-frames"),
                },
            ],
            "specific": [
                {"name": "Goatee", "desc": "Slims and elongates face"},
                {"name": "Light Stubble", "desc": "Defined, clean edges"},
                {"name": "Van Dyke", "desc": "Adds chin length"},
            ],
            "specific_label": "Beard Style",
            "tip": (
                "Avoid round or bowl cuts. Go for angular styles that add height and definition."
            ),
        },
        "Square": {
            "hairstyle": [
                {
                    "name": "Textured Crop",
                    "desc": "Softens the jawline",
                    "image": _h("male", "textured-crop"),
                },
                {
                    "name": "Side Part",
                    "desc": "Breaks the angular look",
                    "image": _h("male", "side-part"),
                },
                {
                    "name": "Curly Medium",
                    "desc": "Adds softness naturally",
                    "image": _h("male", "curly-medium"),
                },
                {
                    "name": "Medium Waves",
                    "desc": "Tapered sides, soft top",
                    "image": _h("male", "medium-waves"),
                },
            ],
            "glasses": [
                {
                    "name": "Round Frames",
                    "desc": "Softens angular jawline",
                    "image": _g("round-frames"),
                },
                {
                    "name": "Oval Frames",
                    "desc": "Gentle, subtle contrast",
                    "image": _g("oval-frames"),
                },
                {"name": "Rimless", "desc": "Subtle and lightweight", "image": _g("rimless")},
            ],
            "specific": [
                {"name": "Light Stubble", "desc": "Maintains shape lightly"},
                {"name": "Short Beard", "desc": "Trimmed close and neat"},
                {"name": "Fade Beard", "desc": "Gradual fade on sides"},
            ],
            "specific_label": "Beard Style",
            "tip": (
                "Your strong jawline is an asset. Soften it with textured or wavy styles rather "
                "than harsh cuts."
            ),
        },
    },
    "female": {
        "Heart": {
            "hairstyle": [
                {
                    "name": "Long Waves",
                    "desc": "Adds width at jaw level",
                    "image": _h("female", "long-waves"),
                },
                {
                    "name": "Layered Lob",
                    "desc": "Balances the wide forehead",
                    "image": _h("female", "layered-lob"),
                },
                {
                    "name": "Curtain Bangs",
                    "desc": "De-emphasizes wide forehead",
                    "image": _h("female", "curtain-bangs"),
                },
                {
                    "name": "Side Swept",
                    "desc": "Draws attention to mid-face",
                    "image": _h("female", "side-swept-f"),
                },
            ],
            "glasses": [
                {"name": "Cat-Eye", "desc": "Complements high cheekbones", "image": _g("cat-eye")},
                {
                    "name": "Oval Frames",
                    "desc": "Softens the chin area",
                    "image": _g("oval-frames"),
                },
                {"name": "Rimless", "desc": "Light, doesn't add weight", "image": _g("rimless")},
            ],
            "specific": [
                {"name": "Contour Temples", "desc": "Narrow the forehead"},
                {"name": "Highlight Chin", "desc": "Add width to lower face"},
                {"name": "Bold Lip Color", "desc": "Draw attention downward"},
            ],
            "specific_label": "Makeup Tips",
            "tip": (
                "Draw attention to your cheekbones. Styles that add volume near the chin balance "
                "your heart shape."
            ),
        },
        "Oblong": {
            "hairstyle": [
                {
                    "name": "Beach Waves",
                    "desc": "Adds soft width to face",
                    "image": _h("female", "beach-waves"),
                },
                {
                    "name": "Blunt Bob",
                    "desc": "Shortens face appearance",
                    "image": _h("female", "blunt-bob"),
                },
                {
                    "name": "Curtain Bangs",
                    "desc": "Reduces face length visually",
                    "image": _h("female", "curtain-bangs"),
                },
                {
                    "name": "Textured Lob",
                    "desc": "Layers with outward movement",
                    "image": _h("female", "textured-lob-f"),
                },
            ],
            "glasses": [
                {"name": "Cat-Eye", "desc": "Broadens the upper face", "image": _g("cat-eye")},
                {"name": "Wayfarer", "desc": "Wide frames add balance", "image": _g("wayfarer")},
                {
                    "name": "Square Frames",
                    "desc": "Bold horizontal statement",
                    "image": _g("square-frames"),
                },
            ],
            "specific": [
                {"name": "Horizontal Blush", "desc": "Adds width across cheeks"},
                {"name": "Bold Brows", "desc": "Shortens face visually"},
                {"name": "Horizontal Liner", "desc": "Widens the eye area"},
            ],
            "specific_label": "Makeup Tips",
            "tip": (
                "Horizontal lines are your best friend. Styles that add width will beautifully "
                "balance your face."
            ),
        },
        "Oval": {
            "hairstyle": [
                {
                    "name": "Long Straight",
                    "desc": "Classic and elegant",
                    "image": _h("female", "long-straight"),
                },
                {
                    "name": "Pixie Cut",
                    "desc": "Shows off balanced features",
                    "image": _h("female", "pixie-cut"),
                },
                {
                    "name": "Layered Lob",
                    "desc": "Modern and chic",
                    "image": _h("female", "layered-lob"),
                },
                {
                    "name": "Beach Waves",
                    "desc": "Effortlessly beautiful",
                    "image": _h("female", "beach-waves"),
                },
            ],
            "glasses": [
                {"name": "Wayfarer", "desc": "Timeless classic", "image": _g("wayfarer")},
                {"name": "Cat-Eye", "desc": "Bold statement frames", "image": _g("cat-eye")},
                {
                    "name": "Rectangular",
                    "desc": "Clean professional look",
                    "image": _g("rectangular"),
                },
            ],
            "specific": [
                {"name": "Soft Contour", "desc": "Enhances natural structure"},
                {"name": "Any Lip Color", "desc": "All shades suit you"},
                {"name": "Experiment Freely", "desc": "Most looks will suit you"},
            ],
            "specific_label": "Makeup Tips",
            "tip": (
                "You have the most balanced face shape. Embrace your versatility and experiment "
                "boldly."
            ),
        },
        "Round": {
            "hairstyle": [
                {
                    "name": "Long Layers",
                    "desc": "Elongates the face",
                    "image": _h("female", "long-waves"),
                },
                {
                    "name": "High Ponytail",
                    "desc": "Adds height visually",
                    "image": _h("female", "high-ponytail"),
                },
                {
                    "name": "Long Straight",
                    "desc": "Slimming effect",
                    "image": _h("female", "long-straight"),
                },
                {
                    "name": "Side Swept",
                    "desc": "Creates asymmetry and length",
                    "image": _h("female", "side-swept-f"),
                },
            ],
            "glasses": [
                {
                    "name": "Rectangular",
                    "desc": "Adds definition to face",
                    "image": _g("rectangular"),
                },
                {"name": "Cat-Eye", "desc": "Lifts and elongates", "image": _g("cat-eye")},
                {
                    "name": "Angular Rect",
                    "desc": "Strong angular contrast",
                    "image": _g("angular-rect"),
                },
            ],
            "specific": [
                {"name": "Contour Sides", "desc": "Slim the face sides"},
                {"name": "Angled Blush", "desc": "Toward the temples"},
                {"name": "Bold Brows", "desc": "Draw the eye upward"},
            ],
            "specific_label": "Makeup Tips",
            "tip": (
                "Create length with vertical lines. High hairstyles and angled makeup beautifully "
                "elongate your face."
            ),
        },
        "Square": {
            "hairstyle": [
                {
                    "name": "Beach Waves",
                    "desc": "Add femininity to features",
                    "image": _h("female", "beach-waves"),
                },
                {
                    "name": "Long Waves",
                    "desc": "Softens the jawline",
                    "image": _h("female", "long-waves"),
                },
                {
                    "name": "Side Swept",
                    "desc": "Breaks the angular forehead",
                    "image": _h("female", "side-swept-f"),
                },
                {
                    "name": "Textured Lob",
                    "desc": "Modern and flattering",
                    "image": _h("female", "textured-lob-f"),
                },
            ],
            "glasses": [
                {"name": "Round Frames", "desc": "Soften angular jaw", "image": _g("round-frames")},
                {"name": "Cat-Eye", "desc": "Draws attention upward", "image": _g("cat-eye")},
                {
                    "name": "Oval Frames",
                    "desc": "Gentle, soft contrast",
                    "image": _g("oval-frames"),
                },
            ],
            "specific": [
                {"name": "Round Blush", "desc": "Softens angular cheeks"},
                {"name": "Soft Smokey Eye", "desc": "Adds femininity"},
                {"name": "Contour Corners", "desc": "Soften the forehead"},
            ],
            "specific_label": "Makeup Tips",
            "tip": (
                "Soft, romantic hairstyles and circular makeup techniques beautifully balance "
                "your angular structure."
            ),
        },
    },
}


def get_recommendations(gender: str, face_shape: str) -> dict:
    gender = gender.lower().strip()
    if gender not in RECOMMENDATIONS:
        raise ValueError(f"Invalid gender '{gender}'.")
    if face_shape not in RECOMMENDATIONS[gender]:
        raise ValueError(f"Unknown face shape '{face_shape}'.")
    return RECOMMENDATIONS[gender][face_shape]
