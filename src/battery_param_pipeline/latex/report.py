import os


class Report:
    def __init__(self, output_dir):
        self.output_dir = output_dir

    def write_parameters(self, parameter_pipeline):
        # initialize
        generated_path = os.path.join(self.output_dir, "latex", "generated")
        contents_file = os.path.join(generated_path, "contents.tex")
        contents = ""

        # generate latex for each component
        for named_component in parameter_pipeline.named_components:
            name, component = named_component

            # add line to contents file
            contents += f"\\input{{generated/{name}.tex}}\n"

            # write latex file for component
            component_file = os.path.join(generated_path, f"{name}.tex")
            component_latex = f"\\subsection{{{name.capitalize()}}}\n\n"
            component_latex += component._generate_latex()
            with open(component_file, "w") as f:
                f.write(component_latex)

        with open(contents_file, "w") as f:
            f.write(contents)
