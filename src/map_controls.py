"""Client-side map presentation controls: no analytics reruns or data transforms."""
import json
from pathlib import Path

import folium
from branca.element import MacroElement, Template


class MapDisplayControl(MacroElement):
    def __init__(self, map_obj):
        super().__init__()
        self._name = "MapDisplayControl"
        # References are Folium-generated identifiers, never user-supplied JavaScript.
        layers = ",".join(
            f"{json.dumps(child.layer_name)}:{child.get_name()}"
            for child in map_obj._children.values()
            if isinstance(child, folium.TileLayer) and not child.overlay
        )
        source = (Path(__file__).resolve().parent.parent / "app/assets/map-interface.js").read_text(encoding="utf-8")
        source = source.replace("__FLOODER_MAP__", "{{ this._parent.get_name() }}")
        source = source.replace("__FLOODER_BASEMAPS__", "{" + layers + "}")
        source = source.replace("__FLOODER_HOME__", json.dumps([*map_obj.location, map_obj.options.get("zoom", 10)]))
        self._template = Template("{% macro script(this, kwargs) %}" + source + "{% endmacro %}")
