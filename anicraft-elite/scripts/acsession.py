"""AniCraft live session driver (anicraft-cli serve): one document, JSON in/out, real ids back.

    from acsession import AniCraft
    with AniCraft() as ac:                      # or AniCraft("shot.anicraft")
        lay = ac.run("layer.new", name="Hero")["layer"]
        ac.at(lay, 0)                           # active layer + playhead, ALWAYS before editing
        ...
Errors raise AniCraftError with the engine's message. Frames are 0-based (engine), not CLI 1-based.
Tested with anicraft-cli 0.2.1 on Windows (2026-11-13).
"""
import json, os, subprocess, tempfile

CLI = os.environ.get("ANICRAFT_CLI", r"C:\Program Files\ArtCraft\AniCraft\anicraft-cli.exe")


class AniCraftError(RuntimeError):
    pass


class AniCraft:
    def __init__(self, doc=None, sample=False, plugins=None):
        args = [CLI, "serve"]
        if sample:
            args.append("--sample")
        elif doc:
            args.append(os.path.abspath(doc))
        if plugins:
            args += ["--plugins", plugins]
        self._err = tempfile.TemporaryFile()
        self.p = subprocess.Popen(args, stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=self._err,
                                  text=True, encoding="utf-8", bufsize=1)
        first = self.p.stdout.readline()
        if not first or not json.loads(first).get("ready"):
            raise AniCraftError("serve did not start: " + first)
        self.n = 0
        self.log = []  # (cmd, params, result) for audit

    def run(self, cmd, params=None, **kw):
        """Run one engine command. Use params={...} for keys that are Python keywords (e.g. "from")."""
        params = dict(params or {}, **kw)
        self.n += 1
        self.p.stdin.write(json.dumps({"id": self.n, "cmd": cmd, "params": params}) + "\n")
        self.p.stdin.flush()
        line = self.p.stdout.readline()
        if not line:
            self._err.seek(0)
            raise AniCraftError(f"{cmd}: serve exited: {self._err.read()[-500:]!r}")
        r = json.loads(line)
        if not r.get("ok"):
            raise AniCraftError(f"{cmd} {params}: {r.get('error')}")
        self.log.append((cmd, params, r.get("result")))
        return r.get("result")

    def at(self, layer, frame, select=False):
        """Make `layer` active and move the playhead to `frame` (0-based). Commands act HERE."""
        self.run("timeline.goto", frame=frame)
        return self.run("layer.select", layer=layer, select=select)

    def key(self, layer, frame, blank=False):
        """Keyframe on `layer` at `frame`, then stand on it (insert_keyframe does not move the playhead)."""
        self.run("timeline.insert_blank_keyframe" if blank else "timeline.insert_keyframe", layer=layer, frame=frame)
        return self.at(layer, frame)

    def layer_len(self, layer):
        for L in self.info()["layers"]:
            if L["id"] == layer:
                ks = L["keyframes"]
                return ks[-1]["start"] + ks[-1]["duration"] if ks else 0
        raise AniCraftError(f"no layer {layer} on this timeline")

    def fit(self, layer, n):
        """Make `layer` exactly `n` frames long (adds or removes frames at its end); verified."""
        cur = self.layer_len(layer)
        if cur < n:
            self.run("timeline.insert_frame", layer=layer, frame=cur, count=n - cur)
        elif cur > n:
            self.run("timeline.remove_frame", layer=layer, frame=n, count=cur - n)
        got = self.layer_len(layer)
        if got != n:
            raise AniCraftError(f"fit: layer {layer} is {got} frames, wanted {n}")
        return got

    def layer_id(self, name):
        for L in self.info()["layers"]:
            if L["name"] == name:
                return L["id"]
        raise AniCraftError(f"no layer named {name!r}")

    def info(self):
        return self.run("doc.info")

    def close(self):
        try:
            self.p.stdin.write(json.dumps({"cmd": "quit"}) + "\n")
            self.p.stdin.flush()
            self.p.wait(timeout=10)
        except Exception:
            self.p.kill()

    def __enter__(self):
        return self

    def __exit__(self, *a):
        self.close()
