#!/usr/bin/env python3
"""Offline regression tests: python -m unittest discover -s tests -v"""
import copy
import json
import sys
import tempfile
import unittest
from pathlib import Path

SKILL = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(SKILL / "scripts"))

from validate_project import validate_bundle, load_bundle
from build_prompt import compile_bundle, assets_for_shot
from export_prompt_pack import export_episode
from review_artifact import approve


def load_template(name):
    return json.loads((SKILL/"templates"/name).read_text(encoding="utf-8"))


class PromptOnlyV1Tests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)/"my-series"
        self.epdir = self.root/"episodes"/"ep001"
        self.epdir.mkdir(parents=True)
        self.series = load_template("series.json")
        self.episode = load_template("episode.json")
        self.shots = load_template("shots.json")
        self.paths = [
            self.root/"series.json", self.epdir/"episode.json", self.epdir/"shots.json"
        ]
        self.persist()

    def persist(self):
        for path, obj in zip(self.paths, (self.series, self.episode, self.shots)):
            path.write_text(json.dumps(obj,ensure_ascii=False,indent=2),encoding="utf-8")

    def issues(self):
        return validate_bundle(self.series,self.episode,self.shots,self.root)

    def compile(self):
        return compile_bundle(
            self.series,self.episode,self.shots,*self.paths,self.epdir/"prompts"
        )

    def test_baseline_prompts_are_model_neutral_and_no_generation(self):
        self.assertFalse([x for x in self.issues() if x["severity"]=="ERROR"])
        manifest=self.compile()
        self.assertEqual(len(manifest["prompts"]),4)
        text=(self.epdir/"prompts"/"sh001.video.md").read_text(encoding="utf-8")
        self.assertIn("pointed canine ears",text)
        self.assertIn("[START STATE]",text)
        self.assertIn("[END STATE]",text)
        self.assertIn("stylized_3d",text)
        self.assertNotIn("@material",text)
        self.assertFalse((self.epdir/"tasks.json").exists())
        self.assertTrue((self.epdir/"prompts"/"sh001.first-frame.md").exists())

    def test_reference_selection_and_real_asset_path(self):
        img=self.root/"assets"/"characters"/"dog_officer_a"/"face.png"
        img.parent.mkdir(parents=True,exist_ok=True)
        img.write_bytes(b"test-reference-file")
        refs=[{"asset_id":"a_face","type":"face_closeup","path":"assets/characters/dog_officer_a/face.png"}]
        self.series["characters"][0]["reference_assets"]=refs
        self.shots["shots"][1]["framing"]="face close-up"
        self.persist()
        self.assertFalse([x for x in self.issues() if x["severity"]=="ERROR"])
        chosen=assets_for_shot(self.series,self.shots["shots"][1])
        self.assertEqual(chosen[0]["asset_id"],"a_face")
        text=(self.epdir/"prompts"/"sh002.video.md")
        self.compile()
        self.assertIn("a_face",text.read_text(encoding="utf-8"))

    def test_missing_asset_is_blocking(self):
        self.series["characters"][0]["reference_assets"]=[
            {"asset_id":"missing_face","type":"face_closeup","path":"assets/characters/dog_officer_a/no-such-file.png"}
        ]
        self.assertIn("MISSING_ASSET",[d["code"] for d in self.issues()])

    def test_traversal_asset_and_shot_id_are_rejected(self):
        self.series["characters"][0]["reference_assets"]=[
            {"asset_id":"outside","type":"front","path":"../../somewhere.png"}
        ]
        self.shots["shots"][0]["shot_id"]="../escape"
        codes={d["code"] for d in self.issues()}
        self.assertIn("UNSAFE_ASSET_PATH",codes)
        self.assertIn("DUPLICATE_SHOT",codes)

    def test_continuity_and_timing_conflicts(self):
        self.shots["shots"][1]["action"]["continuity_in"]["right_hand"]="holding phone"
        self.shots["shots"][1]["time"]["start_s"]=5
        codes={d["code"] for d in self.issues()}
        self.assertIn("CONTINUITY_STATE_CONFLICT",codes)
        self.assertIn("TIMELINE_GAP_OR_OVERLAP",codes)

    def test_draft_export_approval_gate_and_stale_detection(self):
        self.compile()
        with self.assertRaisesRegex(ValueError,"review.json missing"):
            export_episode(self.epdir,self.epdir/"export")
        count=export_episode(self.epdir,self.epdir/"export",allow_draft=True)
        self.assertEqual(count,4)
        self.assertIn("DRAFT", (self.epdir/"export"/"shot-list.md").read_text(encoding="utf-8"))
        for artifact in ("series","episode","shots","prompts"):
            approve(self.epdir,artifact)
        self.assertEqual(export_episode(self.epdir,self.epdir/"export"),4)
        self.series["characters"][0]["identity_lock"]["must_keep"].append("a blue badge on chest")
        self.persist()
        with self.assertRaisesRegex(ValueError,"stale"):
            export_episode(self.epdir,self.epdir/"export")
        # Recompiling a new prompt alone must NOT reuse the previous human approval.
        self.compile()
        with self.assertRaisesRegex(ValueError,"stale"):
            export_episode(self.epdir,self.epdir/"export")
        for artifact in ("series","episode","shots","prompts"):
            approve(self.epdir,artifact)
        self.assertEqual(export_episode(self.epdir,self.epdir/"export"),4)

    def test_2d_regression_does_not_force_3d(self):
        self.series["visual_style"]["medium"]="2d_anime"
        self.series["visual_style"]["description"]="2D cel animation with soft watercolor backgrounds"
        self.series["visual_style"]["negative_style"]=["no 3D render"]
        self.persist()
        self.compile()
        prompt=(self.epdir/"prompts"/"sh001.video.md").read_text(encoding="utf-8")
        self.assertIn("2d_anime",prompt)
        self.assertIn("no 3D render",prompt)
        self.assertNotIn("stylized_3d",prompt)


if __name__ == "__main__":
    unittest.main()
