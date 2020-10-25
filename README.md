[![Code style: black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/psf/black)

# Automatic Generation of Type-and-Rule-Annotated qtree Trees with Python

The script is a very simple program that parses LaTeX [TikZ qtree](https://ctan.org/pkg/tikz-qtree?lang=en)<sup id="a1">[1](#f1)</sup> strings and outputs the same tree annotated with semantic types and the rules of composition (Heim-&-Kratzer-style) that led to that type. Being simple, the script comes with a number of restrictions some of which I'll detail below.

As an aside, my implementation is the offspring of a desire to program, rather than one to innovate. There are certainly better and more thought-out alternatives around.

<b id="f1">1</b> For TikZ itself, see https://www.ctan.org/pkg/pgf. [↩](#a1)

## Getting Started

```python
# lexicon that includes the semantic types
lex = {"e": ["Andrew", "Mathis"], "<e, t>": ["hits"]}

# define the tree that is to be annotated
tree_string = "[.\\node(top){S}; [.NP^1 [.N^1 Andrew ] ] [.VP [.V hits ] [.NP^2 [.N^2 Mathis ] ] ] ]"

# save the output to a LaTeX file
with open("LaTeX/treeparses.tex", "w") as f:
    f.write(tree_to_latex(tree_string, lex))
```

## On Composition Errors

Though not shown here, composition errors are colorized differently from the other nodes by default. That is to say that composition errors (e.g. where a two nodes of type `e` are sisters) will not cause the script to crash (or complain). Instead, the rules and types of these nodes will be marked with "?" and colored in red.

## Examples

### Single Image

The input string in (1) produces the output below (once the corresponding (Xe)LaTeX code is compiled to pdf). Note that LaTeX functions need to be escaped (`\\node` instead of the LaTeX-native `\node`). The top node specification can be left out completely, however.

1. `[.\\node(top){S}; [.NP^1 [.N^1 Andrew ] ] [.VP [.V hits ] [.NP^2 [.N^2 Mathis ] ] ] ]`

<p align="center">
<img src="https://github.com/mkthalmann/rule-and-type-parse/blob/master/media/sample.jpg" width="448" height="490">
</p>

### Multipage PDF

<p align="center">
<img src="https://github.com/mkthalmann/rule-and-type-parse/blob/master/media/semtree.gif" width="800">
</p>

## Restrictions

* Nodes labels in the tree should be unique:
  * `[.S [.NP [.N Mary ] ] [.VP [.V hits ] [.NP [.N Peter ] ] ] ]` would be illicit because both `NP` and `N` occur twice. More precisely, they would not be illicit, but they will not be distinguished by the script. If they bear the same logical type and are composed by the same rules, that does not matter, however (as is the case here). Thus, it is probably better to simply use superscript to have unique node labels.
* Lexical entries and the nodes corresponding to them must match exactly: the look-up is case sensitive (though there will be a warning if a lower-case or capitalized version of an input node exists) and does not recognize inflectional suffixes or the like (rectifying this would probably involve tokenizing, which is not in the scope of this project).
* ambiguous lexical entries need to individuated via non-numerical subscripts (e.g. `that_{RP}` and `that_{dem}`). While I want to handle lexical ambiguity in a more elegant way in the future, subscripting is the only option for now.

## License

<a rel="license" href="http://creativecommons.org/licenses/by-sa/4.0/"><img alt="Creative Commons License" style="border-width:0" src="https://i.creativecommons.org/l/by-sa/4.0/88x31.png" /></a><br />This work is licensed under a <a rel="license" href="http://creativecommons.org/licenses/by-sa/4.0/">Creative Commons Attribution-ShareAlike 4.0 International License</a>.

## Feedback

If you have any comments, feature requests or suggestions, please feel free to send me an [e-mail](mailto:maik.thalmann@gmail.com?subject=[GitHub]%20SemTrees).
