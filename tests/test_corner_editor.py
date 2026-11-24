import numpy as np
from scanpdf.gui.corner_editor import fit_box, CornerEditor
from types import SimpleNamespace


def test_letterbox_drag() -> None:
    """A drag through a letterboxed preview maps into source pixels."""
    assert fit_box((801,401), (401,401)) == (0,100,401,201)
    editor = SimpleNamespace(active=0, points=np.zeros((4,2)), source=(801,401),
                             origin=np.array([0,100]), scale=np.array([0.5,0.5]),
                             changed=lambda: None, _overlay=lambda: None)
    CornerEditor._drag(editor, SimpleNamespace(x=200,y=150))
    np.testing.assert_equal(editor.points[0], [400,100])
