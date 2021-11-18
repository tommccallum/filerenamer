import unittest
import filerename

class FileRenamerTest(unittest.TestCase):

    def test_createDefaultConfig(self):
        config = filerename.createConfig()
        self.assertEqual(config.testMode, True)

    def test_renameEmptyString(self):
        config = filerename.createConfig()
        actual = filerename.renameString(config, "")
        expected = ""
        self.assertEqual(expected, actual)

    def test_renameStringAbc(self):
        config = filerename.createConfig()
        actual = filerename.renameString(config, "abc")
        expected = "abc"
        self.assertEqual(expected, actual)

    def test_renameStringWithColon(self):
        config = filerename.createConfig()
        actual = filerename.renameString(config, "abc : def")
        expected = "abc  def"
        self.assertEqual(expected, actual)

    def test_renameStringWithOpenBracket(self):
        config = filerename.createConfig()
        actual = filerename.renameString(config, "abc (def)")
        expected = "abc - def)"
        self.assertEqual(expected, actual)

    def test_createConfigWithFile(self):
        config = filerename.createConfig("filerename.json")
        self.assertEqual(config.testMode, True)
        self.assertGreater(len(config.remove), 0 )
        self.assertGreater(len(config.replace), 0)

if __name__ == '__main__':
    unittest.main()