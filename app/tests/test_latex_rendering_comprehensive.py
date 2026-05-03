"""LaTeX渲染完整性测试

测试重点：
1. 数学公式正确保留（$...$和$$...$$）
2. 非数学LaTeX命令完全清理
3. LaTeX残留检测（\\textbf, \\begin, \\cite等）
4. HTML标签清理
5. 文字拼接防护
6. 特殊字符处理
7. 实际输出验证
"""
import pytest
import re
from core.text_sanitize import strip_non_math_latex, sanitize_dict


class TestMathPreservation:
    """数学公式保留测试"""

    def test_inline_math_single(self):
        """测试：单个行内公式应该完整保留"""
        cases = [
            ("The value is $x$", "$x$"),
            ("Function $f(x) = x^2$", "$f(x) = x^2$"),
            ("Limit $\\lim_{n \\to \\infty} a_n$", "$\\lim_{n \\to \\infty} a_n$"),
            ("Integral $\\int_0^1 f(x) dx$", "$\\int_0^1 f(x) dx$"),
        ]

        for input_text, expected_math in cases:
            output = strip_non_math_latex(input_text)
            assert expected_math in output, f"数学公式丢失: {expected_math} in {output}"

    def test_inline_math_multiple(self):
        """测试：多个行内公式应该全部保留"""
        input_text = "Given $a$ and $b$, prove $a + b = c$"
        output = strip_non_math_latex(input_text)

        assert "$a$" in output
        assert "$b$" in output
        assert "$a + b = c$" in output

    def test_display_math_single(self):
        """测试：显示公式应该完整保留"""
        cases = [
            ("$$x^2 + y^2 = z^2$$", "$$x^2 + y^2 = z^2$$"),
            ("$$\\int_0^\\infty e^{-x} dx = 1$$", "$$\\int_0^\\infty e^{-x} dx = 1$$"),
            ("$$\\sum_{i=1}^n i = \\frac{n(n+1)}{2}$$", "$$\\sum_{i=1}^n i = \\frac{n(n+1)}{2}$$"),
        ]

        for input_text, expected_math in cases:
            output = strip_non_math_latex(input_text)
            assert expected_math in output

    def test_mixed_inline_and_display_math(self):
        """测试：混合行内和显示公式都应该保留"""
        input_text = "Consider $f(x)$ where $$f(x) = \\int_0^x g(t) dt$$"
        output = strip_non_math_latex(input_text)

        assert "$f(x)$" in output
        assert "$$f(x) = \\int_0^x g(t) dt$$" in output

    def test_math_with_complex_latex(self):
        """测试：复杂LaTeX数学公式应该保留"""
        complex_math = [
            r"$\frac{\partial^2 u}{\partial t^2} = c^2 \nabla^2 u$",
            r"$\mathbb{E}[X] = \int_{-\infty}^{\infty} x f(x) dx$",
            r"$$\begin{pmatrix} a & b \\ c & d \end{pmatrix}$$",
        ]

        for math in complex_math:
            output = strip_non_math_latex(math)
            # 数学环境内的命令应该保留
            assert r"\frac" in output or r"\partial" in output or r"\begin{pmatrix}" in output or r"\mathbb" in output


class TestLaTeXRemoval:
    """LaTeX命令移除测试"""

    def test_text_formatting_commands_removed(self):
        """测试：文本格式化命令应该被移除"""
        cases = [
            (r"\textbf{bold text}", "bold text"),
            (r"\emph{emphasized}", "emphasized"),
            (r"\textit{italic}", "italic"),
            (r"\underline{underlined}", "underlined"),
            (r"\texttt{monospace}", "monospace"),
        ]

        for input_text, expected_content in cases:
            output = strip_non_math_latex(input_text)
            # 命令应该被移除
            assert "\\textbf" not in output
            assert "\\emph" not in output
            assert "\\textit" not in output
            # 但内容应该保留
            assert expected_content.split()[0] in output

    def test_citation_commands_removed(self):
        """测试：引用命令应该被完全移除"""
        cases = [
            r"\cite{smith2020}",
            r"\ref{eq:1}",
            r"\eqref{eq:main}",
            r"\label{thm:1}",
        ]

        for input_text in cases:
            output = strip_non_math_latex(input_text)
            # 引用命令及其内容应该被移除
            assert "\\cite" not in output
            assert "\\ref" not in output
            assert "\\eqref" not in output
            assert "\\label" not in output

    def test_environment_tags_removed(self):
        """测试：环境标签应该被移除但内容保留"""
        cases = [
            (r"\begin{theorem}Content\end{theorem}", "Content"),
            (r"\begin{proof}Proof text\end{proof}", "Proof text"),
            (r"\begin{lemma}Lemma content\end{lemma}", "Lemma content"),
        ]

        for input_text, expected_content in cases:
            output = strip_non_math_latex(input_text)
            # 环境标签应该被移除
            assert "\\begin{theorem}" not in output
            assert "\\end{theorem}" not in output
            # 但内容应该保留
            assert expected_content in output or expected_content.split()[0] in output

    def test_section_commands_removed(self):
        """测试：章节命令应该被移除"""
        cases = [
            r"\section{Introduction}",
            r"\subsection{Background}",
            r"\chapter{Chapter 1}",
        ]

        for input_text in cases:
            output = strip_non_math_latex(input_text)
            assert "\\section" not in output
            assert "\\subsection" not in output
            assert "\\chapter" not in output


class TestHTMLCleaning:
    """HTML清理测试"""

    def test_html_tags_removed(self):
        """测试：HTML标签应该被移除"""
        cases = [
            ("<strong>bold</strong>", "bold"),
            ("<em>italic</em>", "italic"),
            ("<div>content</div>", "content"),
            ("<span class='test'>text</span>", "text"),
            ("<p>paragraph</p>", "paragraph"),
        ]

        for input_text, expected_content in cases:
            output = strip_non_math_latex(input_text)
            # HTML标签应该被移除
            assert "<strong>" not in output
            assert "<em>" not in output
            assert "<div>" not in output
            # 但内容应该保留
            assert expected_content in output

    def test_html_entities_cleaned(self):
        """测试：HTML实体应该被清理"""
        cases = [
            ("&nbsp;&nbsp;text", "text"),
            ("&lt;test&gt;", "<test>"),
            ("&amp;", "&"),
            ("&quot;quote&quot;", '"quote"'),
        ]

        for input_text, expected_pattern in cases:
            output = strip_non_math_latex(input_text)
            # HTML实体应该被转换或移除
            assert "&nbsp;" not in output or "  " in output
            assert "&lt;" not in output or "<" in output

    def test_html_table_structures_removed(self):
        """测试：HTML表格结构应该被移除"""
        input_html = "<table><tr><td>cell1</td><td>cell2</td></tr></table>"
        output = strip_non_math_latex(input_html)

        # 标签应该被移除
        assert "<table>" not in output
        assert "<tr>" not in output
        assert "<td>" not in output
        # 内容应该保留
        assert "cell1" in output or "cell2" in output


class TestNoTextConcatenation:
    """文字拼接防护测试"""

    def test_latex_removal_adds_spaces(self):
        """测试：移除LaTeX后应该添加空格防止拼接"""
        cases = [
            (r"word1\textbf{word2}word3", ["word1", "word2", "word3"]),
            (r"text\cite{ref}more", ["text", "more"]),
            (r"a\label{x}b", ["a", "b"]),
        ]

        for input_text, expected_words in cases:
            output = strip_non_math_latex(input_text)
            # 不应该拼接成一个单词
            for i in range(len(expected_words) - 1):
                w1, w2 = expected_words[i], expected_words[i+1]
                assert f"{w1}{w2}" not in output, f"文字拼接: {w1}{w2} found in {output}"

    def test_multiple_consecutive_spaces_cleaned(self):
        """测试：连续多个空格应该被清理"""
        input_text = r"text1\textbf{text2}\emph{text3}text4"
        output = strip_non_math_latex(input_text)

        # 不应该有连续3个以上的空格
        assert "   " not in output or output.count("   ") <= 1


class TestLatexResidueDetection:
    """LaTeX残留检测测试"""

    def test_no_backslash_commands_outside_math(self):
        """测试：数学环境外不应该有反斜杠命令"""
        test_inputs = [
            r"Text with \textbf{bold} and $x^2$",
            r"Reference \cite{paper} and formula $a+b$",
            r"\begin{theorem}Content\end{theorem} and $$x=1$$",
        ]

        for input_text in test_inputs:
            output = strip_non_math_latex(input_text)

            # 移除数学部分后检查
            without_math = re.sub(r'\$\$.*?\$\$|\$.*?\$', '', output)

            # 不应该有这些命令
            assert "\\textbf" not in without_math
            assert "\\cite" not in without_math
            assert "\\begin{" not in without_math
            assert "\\end{" not in without_math

    def test_no_curly_braces_outside_math(self):
        """测试：数学环境外不应该有多余的花括号"""
        input_text = r"Text with \textbf{bold}"
        output = strip_non_math_latex(input_text)

        # 移除数学部分
        without_math = re.sub(r'\$\$.*?\$\$|\$.*?\$', '', output)

        # 应该没有孤立的花括号
        assert without_math.count('{') == without_math.count('}') == 0

    def test_no_latex_environments(self):
        """测试：不应该有LaTeX环境残留"""
        environments = [
            "theorem", "proof", "lemma", "definition",
            "equation", "align", "array"
        ]

        input_text = r"\begin{theorem}Test\end{theorem} and $x$"
        output = strip_non_math_latex(input_text)

        for env in environments:
            assert f"\\begin{{{env}}}" not in output
            assert f"\\end{{{env}}}" not in output


class TestRealWorldScenarios:
    """真实场景测试"""

    def test_academic_paper_abstract(self):
        """测试：学术论文摘要"""
        input_text = r"""
        \textbf{Abstract.} We prove that for any $n \in \mathbb{N}$,
        the function $f(x) = x^n$ is \emph{continuous}.
        See \cite{smith2020} for details. The key result is
        $$\lim_{h \to 0} \frac{f(x+h) - f(x)}{h} = nx^{n-1}$$
        """

        output = strip_non_math_latex(input_text)

        # 数学应该保留
        assert "$n \\in \\mathbb{N}$" in output
        assert "$f(x) = x^n$" in output
        assert "$$\\lim_{h \\to 0}" in output

        # LaTeX命令应该被移除
        assert "\\textbf" not in output
        assert "\\emph" not in output
        assert "\\cite" not in output

        # 内容应该保留
        assert "Abstract" in output
        assert "continuous" in output

    def test_theorem_statement_with_proof(self):
        """测试：定理陈述和证明"""
        input_text = r"""
        \begin{theorem}
        Every \textbf{continuous} function $f: [a,b] \to \mathbb{R}$
        attains its maximum.
        \end{theorem}
        \begin{proof}
        Use \cite{bolzano} and $\epsilon$-$\delta$ argument.
        \end{proof}
        """

        output = strip_non_math_latex(input_text)

        # 数学保留
        assert "$f: [a,b] \\to \\mathbb{R}$" in output
        assert "$\\epsilon$" in output
        assert "$\\delta$" in output

        # 环境标签移除
        assert "\\begin{theorem}" not in output
        assert "\\end{proof}" not in output

        # 引用移除
        assert "\\cite" not in output

        # 内容保留
        assert "continuous" in output
        assert "maximum" in output

    def test_mixed_content_with_html_and_latex(self):
        """测试：混合HTML和LaTeX的内容"""
        input_text = r"""
        <div class="result">
        The <strong>main theorem</strong> states that $\forall n \in \mathbb{N}$,
        we have $n^2 \geq n$. \cite{ref1}
        <table><tr><td>$x$</td><td>$x^2$</td></tr></table>
        </div>
        """

        output = strip_non_math_latex(input_text)

        # 数学保留
        assert "$\\forall n \\in \\mathbb{N}$" in output
        assert "$n^2 \\geq n$" in output
        assert "$x$" in output
        assert "$x^2$" in output

        # HTML和LaTeX移除
        assert "<div>" not in output
        assert "<strong>" not in output
        assert "<table>" not in output
        assert "\\cite" not in output


class TestEdgeCases:
    """边界情况测试"""

    def test_empty_string(self):
        """测试：空字符串"""
        assert strip_non_math_latex("") == ""

    def test_none_value(self):
        """测试：None值"""
        assert strip_non_math_latex(None) is None

    def test_only_math(self):
        """测试：只有数学公式"""
        input_text = "$x^2 + y^2 = z^2$"
        output = strip_non_math_latex(input_text)
        assert output == input_text

    def test_only_latex_commands(self):
        """测试：只有LaTeX命令（无数学）"""
        input_text = r"\textbf{text} \cite{ref}"
        output = strip_non_math_latex(input_text)

        # 命令应该被移除
        assert "\\textbf" not in output
        assert "\\cite" not in output
        # 内容应该保留
        assert "text" in output

    def test_nested_latex_commands(self):
        """测试：嵌套的LaTeX命令"""
        input_text = r"\textbf{\emph{nested}}"
        output = strip_non_math_latex(input_text)

        # 所有命令都应该被移除
        assert "\\textbf" not in output
        assert "\\emph" not in output
        # 内容应该保留
        assert "nested" in output

    def test_malformed_latex(self):
        """测试：格式错误的LaTeX"""
        cases = [
            r"\textbf{unclosed",  # 未闭合的大括号
            r"text}",  # 多余的闭合括号
            r"\unclosed",  # 未闭合的命令
        ]

        for input_text in cases:
            # 不应该崩溃
            output = strip_non_math_latex(input_text)
            assert isinstance(output, str)


class TestDictSanitization:
    """字典清理测试"""

    def test_sanitize_dict_specific_fields(self):
        """测试：只清理指定字段"""
        input_dict = {
            "statement": r"Theorem: $x^2 \geq 0$ for all $x$. \textbf{Important!}",
            "proof": r"Use \cite{ref} and $x \cdot x$",
            "code": r"def f(x): return x**2",  # 不应该被清理
        }

        output = sanitize_dict(input_dict, fields=("statement", "proof"))

        # statement 和 proof 应该被清理
        assert "\\textbf" not in output["statement"]
        assert "\\cite" not in output["proof"]
        assert "$x^2 \\geq 0$" in output["statement"]
        assert "$x \\cdot x$" in output["proof"]

        # code 不应该被清理
        assert output["code"] == input_dict["code"]

    def test_sanitize_nested_dict(self):
        """测试：嵌套字典清理"""
        input_dict = {
            "level1": {
                "level2": {
                    "text": r"\textbf{bold} and $x^2$"
                }
            }
        }

        output = sanitize_dict(input_dict)

        # 应该递归清理
        cleaned_text = output["level1"]["level2"]["text"]
        assert "\\textbf" not in cleaned_text
        assert "$x^2$" in cleaned_text


class TestPerformance:
    """性能测试"""

    def test_large_text_performance(self):
        """测试：大文本处理性能"""
        import time

        # 生成大文本（10KB）
        large_text = (r"Text with $x^2$ and \textbf{bold}. " * 1000)

        start = time.time()
        output = strip_non_math_latex(large_text)
        elapsed = time.time() - start

        # 应该在合理时间内完成（<1秒）
        assert elapsed < 1.0
        assert len(output) > 0

    def test_many_math_formulas_performance(self):
        """测试：大量数学公式处理性能"""
        import time

        # 生成包含大量数学公式的文本
        text = " ".join([f"$x_{i}^2$" for i in range(1000)])

        start = time.time()
        output = strip_non_math_latex(text)
        elapsed = time.time() - start

        # 应该在合理时间内完成
        assert elapsed < 1.0
        # 所有数学公式都应该保留
        assert "$x_" in output


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
