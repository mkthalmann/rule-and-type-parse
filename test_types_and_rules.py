from types_and_rules import *
from lexicon import lex
import unittest


class TestComposition(unittest.TestCase):
    def test_clean_tree(self):
        with self.assertRaises(LaTeXEscapeError):
            clean_tree(
                "[.\node(top){A }; [.B not [.C [.D [.E [.F [.G tanzt ] ] ] ] [.Peter ] ] ] ]"
            )

    def test_find_hierarchy(self):

        # one closing bracket missing
        with self.assertRaises(TreeBracketError):
            find_hierarchy(
                "[.S [.NP [.N Peter ] ] [.VP [.V hits ] [.NP [.N Peter ] ] ]"
            )

        # additional closing bracket
        with self.assertRaises(TreeBracketError):
            find_hierarchy(
                "[.S [.NP [.N Peter ] ] [.VP [.V hits ] [.NP [.N Peter ] ] ] ] ]"
            )

        # one ternary branching node
        with self.assertRaises(TernaryBranchingError):
            find_hierarchy(
                "[.\\node(top){NP}; [.AP schuldiger ] [.AP Schüler ] [.NP Idiot ] ]"
            )

        self.assertEqual(
            find_hierarchy(
                "[.\\node(top){S }; [.NP^1 [.N^1 Andrew ] ] [.VP [.V hits ] [.NP^2 [.N^2 Mathis ] ] ] ]"
            ),
            (
                Tree(
                    "S",
                    [
                        Tree("NP^1", [Tree("N^1", ["Andrew"])]),
                        Tree(
                            "VP",
                            [
                                Tree("V", ["hits"]),
                                Tree("NP^2", [Tree("N^2", ["Mathis"])]),
                            ],
                        ),
                    ],
                ),
                {
                    "S": ["NP^1", "VP"],
                    "NP^1": ["N^1"],
                    "N^1": ["Andrew"],
                    "VP": ["V", "NP^2"],
                    "V": ["hits"],
                    "NP^2": ["N^2"],
                    "N^2": ["Mathis"],
                },
            ),
        )

    def test_compose_all(self):

        # non-terminal daughters that aren't present in the tree structure raise a TreeStructureError
        with self.assertRaises(TreeStructureError):
            compose_all({"S": ["NP", "tanzt"]}, lex, 15)

        # terminal nodes which are not specified in the lexicon raise a LexiconError
        with self.assertRaises(LexiconError):
            compose_all(
                {"S": ["NP", "VP"], "NP": ["Klaus"], "VP": ["schmörlt"]}, lex, 15
            )


if __name__ == "__main__":
    unittest.main()
