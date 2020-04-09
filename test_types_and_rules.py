from types_and_rules import *
from lexicon import lex
import unittest


class TestComposition(unittest.TestCase):
    def test_clean_tree(self):
        with self.assertRaises(LaTeXEscapeError):
            clean_tree(
                "[.\node(top){A }; [.B not [.C [.D [.E [.F [.G tanzt ] ] ] ] [.Peter ] ] ] ]"
            )

    def test_check_tree(self):
        with self.assertRaises(TernaryBranchingError):
            check_tree({"S": ["Klaus", "malt", "Maria"]})

    def test_find_hierarchy(self):
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
            compose_all({"S": ["NP", "tanzt"]}, lex)
        # erminal nodes which are not specified in the lexicon raise a LexiconError
        with self.assertRaises(LexiconError):
            compose_all({"S": ["NP", "VP"], "NP": ["Klaus"], "VP": ["schmörlt"]}, lex)
        # type mismatches should raise a CompositionError
        with self.assertRaises(CompositionError):
            compose_all({"S": ["NP", "VP"], "NP": ["alle"], "VP": ["beobachtet"],}, lex)
        # CompositionError because of object quantifier without QR
        with self.assertRaises(CompositionError):
            compose_all(
                {
                    "S": ["NP_1", "VP"],
                    "NP_1": ["N_1"],
                    "N_1": ["Mark"],
                    "VP": ["V'"],
                    "V'": ["V", "NP_2"],
                    "V": ["bought"],
                    "NP_2": ["D", "N_2"],
                    "D": ["all"],
                    "N_2": ["flowers"],
                },
                lex,
            )
            self.assertEqual(
                (
                    {
                        "S": "t",
                        "NP^1": "e",
                        "N^1": "e",
                        "VP": "<e, t>",
                        "V": "<e, <e, t>>",
                        "NP^2": "e",
                        "N^2": "e",
                        "Andrew": "e",
                        "hits": "<e, <e, t>>",
                        "Mathis": "e",
                    },
                    {
                        "S": "FA\\shortleftarrow",
                        "NP^1": "NN",
                        "N^1": "NN",
                        "VP": "FA\\shortrightarrow",
                        "V": "NN",
                        "NP^2": "NN",
                        "N^2": "NN",
                        "Andrew": "TN_1",
                        "hits": "TN_1",
                        "Mathis": "TN_1",
                    },
                ),
                compose_all(
                    find_hierarchy(
                        "[.\\node(top){S }; [.NP^1 [.N^1 Andrew ] ] [.VP [.V hits ] [.NP^2 [.N^2 Mathis ] ] ] ]"
                    )[1],
                    lex,
                ),
            )
            self.assertEqual(
                (
                    {
                        "S": "t",
                        "DP^1": "e",
                        "D^1": "<<e, t>, e>",
                        "NP": "<e, t>",
                        "N$''$": "<e, t>",
                        "N$'$": "<e, t>",
                        "N": "<e, t>",
                        "CP": "<e, t>",
                        "DP^2": "-",
                        "C$'$": "t",
                        "C": "",
                        "S$'$": "t",
                        "$t$": "e",
                        "VP": "<e, t>",
                        "DP^3": "e",
                        "D^3": "<<e, t>, e>",
                        "NP^2": "<e, t>",
                        "N$''$^2": "<e, t>",
                        "N$'$^2": "<e, t>",
                        "N^2": "<e, t>",
                        "PP": "<e, t>",
                        "P": "<e, <e, t>>",
                        "DP^4": "e",
                        "V": "<e, <e, t>>",
                        "VP^2": "<e, t>",
                        "V^2": "<e, t>",
                        "der": "<<e, t>, e>",
                        "Junge": "<e, t>",
                        "der_{RP}": "-",
                        "wo": "",
                        "die": "<<e, t>, e>",
                        "Fee": "<e, t>",
                        "aus": "<e, <e, t>>",
                        "Nimmerland": "e",
                        "belästigt": "<e, <e, t>>",
                        "fliegt": "<e, t>",
                    },
                    {
                        "S": "FA\\shortleftarrow",
                        "DP^1": "FA\\shortrightarrow",
                        "D^1": "NN",
                        "NP": "NN",
                        "N$''$": "PM",
                        "N$'$": "NN",
                        "N": "NN",
                        "CP": "PA",
                        "DP^2": "NN",
                        "C$'$": "NN",
                        "C": "NN",
                        "S$'$": "FA\\shortleftarrow",
                        "$t$": "TN_2",
                        "VP": "FA\\shortleftarrow",
                        "DP^3": "FA\\shortrightarrow",
                        "D^3": "NN",
                        "NP^2": "NN",
                        "N$''$^2": "PM",
                        "N$'$^2": "NN",
                        "N^2": "NN",
                        "PP": "FA\\shortrightarrow",
                        "P": "NN",
                        "DP^4": "NN",
                        "V": "NN",
                        "VP^2": "NN",
                        "V^2": "NN",
                        "der": "TN_1",
                        "Junge": "TN_1",
                        "der_{RP}": "-",
                        "wo": "-",
                        "die": "TN_1",
                        "Fee": "TN_1",
                        "aus": "TN_1",
                        "Nimmerland": "TN_1",
                        "belästigt": "TN_1",
                        "fliegt": "TN_1",
                    },
                ),
                compose_all(
                    find_hierarchy(
                        "[.\\node(top){S }; [.DP^1 [.D^1 der ] [.NP [.N$''$ [.N$'$ [.N Junge ] ] [.CP [.DP^2 der_{RP} ] [.C$'$ [.C wo ] [.S$'$ [.$t$ ] [.VP [.DP^3 [.D^3 die ] [.NP^2 [.N$''$^2 [.N$'$^2 [.N^2 Fee ] ] [.PP [.P aus ] [.DP^4 Nimmerland ] ] ] ] ]  [.V belästigt ] ] ] ] ] ] ] ]  [.VP^2 [.V^2 fliegt ] ] ]"
                    )[1],
                    lex,
                ),
            )


if __name__ == "__main__":
    unittest.main()
