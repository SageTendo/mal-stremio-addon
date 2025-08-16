import unittest

from run import app


class TestManifestBlueprint(unittest.TestCase):
    def setUp(self):
        """
        Set up the test class
        """
        app.config["TESTING"] = True
        app.config["SECRET"] = "Testing Secret"
        self.client = app.test_client()

    def test_manifest(self):
        """
        Test the manifest endpoint
        """
        response = self.client.get("/123/manifest.json")
        self.assertEqual(200, response.status_code)

        manifest = response.json
        self.assertIsNotNone(manifest["id"])
        self.assertIsNotNone(manifest["name"])
        self.assertIsNotNone(manifest["version"])
        self.assertIsNotNone(manifest["logo"])
        self.assertIsNotNone(manifest["description"])
        self.assertIsNotNone(manifest["types"])
        self.assertIsNotNone(manifest["catalogs"])
        self.assertIsNotNone(manifest["behaviorHints"])
        self.assertIsNotNone(manifest["resources"])
        self.assertIsNotNone(manifest["idPrefixes"])

        for catalog in manifest["catalogs"]:
            self.assertEqual(catalog["type"], "anime")
            self.assertIn(
                catalog["id"],
                [
                    "search_list",
                    "plan_to_watch",
                    "watching",
                    "completed",
                    "on_hold",
                    "dropped",
                ],
            )
            self.assertIn(
                catalog["name"],
                [
                    "MAL",
                    "MAL: Plan To Watch",
                    "MAL: Watching",
                    "MAL: Completed",
                    "MAL: On Hold",
                    "MAL: Dropped",
                ],
            )
            for extra in catalog["extra"]:
                self.assertIn(extra["name"], ["skip", "genre", "search"])

                if extra.get("isRequired", None):
                    self.assertTrue(extra["isRequired"])

                if extra.get("options", None):
                    self.assertIsNotNone(extra["options"])

    def test_unconfigured_manifest(self):
        """
        Test the manifest endpoint when the user has not configured the addon
        """
        response = self.client.get("/manifest.json")
        self.assertEqual(200, response.status_code)

        manifest = response.json
        self.assertIn("configurable", manifest["behaviorHints"])
        self.assertTrue(manifest["behaviorHints"]["configurable"])

        self.assertIn("configurationRequired", manifest["behaviorHints"])
        self.assertTrue(manifest["behaviorHints"]["configurationRequired"])

    def test_configured_manifest(self):
        """
        Test the manifest endpoint when the user has configured the addon
        """
        response = self.client.get("/123/manifest.json")
        self.assertEqual(200, response.status_code)

        manifest = response.json
        self.assertIsNotNone(manifest)
