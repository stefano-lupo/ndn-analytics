from typing import List
from reading_utils import readFileSafe

LOG_FILE = "java.log"
ERROR_STRINGS = ["exception", "error [", "Assertion 'IsLocked()"]
# ERROR_STRINGS = ["exception"]
# ERROR_STRINGS = []

IGNORE_STRINGS = ["Type component was null for collision with PROJECTILE"]

class LogReader:

    def __init__(self, node: str, nodeDir: str):
        self.node = node
        self.nodeDir = nodeDir
        lines = readFileSafe(nodeDir, LOG_FILE)
        for i, line in enumerate(lines):
            if self.isErrorString(line):
                print("\n\nEXCEPTION FOUND IN JAVA LOG FILE\n\n")
                toPrint = lines[i:i+10]
                print("".join(toPrint))
                print("Found exception in log file for %s at line %d" % (node, i))
                input("\nPress any key to continue")

    def isErrorString(self, line: str):
        errorStrings = self.toLower(ERROR_STRINGS)
        ignoreStrings = self.toLower(IGNORE_STRINGS)
        lower = line.lower()

        if lower in errorStrings:
            if lower not in ignoreStrings:
                return True


        return False

        # for errorString in ERROR_STRINGS:
        #     if errorString in line.lower():
        #         return True

        # return False


    def toLower(self, lst:List[str]):
        return [s.lower() for s in lst]