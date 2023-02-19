import inspect


def parameter_dict_to_table(d):
    """Convert a dictionary to a latex table."""
    table = [
        r"\begin{center}",
        r"\begin{tabular}{ll}",
        r"\toprule",
        r"Parameter & Value \\",
        r"\midrule",
    ]

    functions = []
    for key, value in d.items():
        if callable(value):
            try:
                function = [
                    f"Function for `{key}':",
                    r"\begin{verbatim}",
                    # add extra \n at the start so that the first line gets unindented
                    ("\n" + inspect.getsource(value)).replace("\n    ", "\n"),
                    r"\end{verbatim}",
                ]
                functions.append("\n".join(function))
            except TypeError:
                pass
        else:
            # default to 4 significant figures for now
            # TODO: track uncertainty and use that
            table.append("\t" + r"{} & {} \\".format(key, f"{value:.4g}"))

    table += [r"\bottomrule", r"\end{tabular}", r"\end{center}"]

    table += ["\n".join(functions)]

    return "\n".join(table)
