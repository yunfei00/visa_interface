import os.path

import yaml
import markdown


def generate_markdown(commands, output_file="visa_commands.md"):
    lines = ["# 仪表 VISA/SCPI 命令手册\n"]

    for category, content in commands.items():
        desc = content.get("description", "")
        lines.append(f"## {category}\n")
        if desc:
            lines.append(f"> {desc}\n")

        groups = content.get("groups", {})
        for group, actions in groups.items():
            lines.append(f"### {group}\n")
            for action, cmd in actions.items():
                lines.append(f"- **{action}** → `{cmd}`")
            lines.append("")
        lines.append("\n---\n")

    with open(output_file, "w", encoding="utf-8") as f:
        f.write("\n".join(lines))
    print(f"✅ 文档已生成: {output_file}")


def generate_html(md_file="visa_commands.md", output_file="visa_commands.html"):
    with open(md_file, "r", encoding="utf-8") as f:
        text = f.read()

    html = markdown.markdown(text, extensions=["tables", "fenced_code"])

    with open(output_file, "w", encoding="utf-8") as f:
        f.write("<html><body>" + html + "</body></html>")
    print(f"✅ HTML 文档已生成: {output_file}")


def generate_python_class(commands, output_file="visa_commands.py"):
    lines = ["# 自动生成的仪表命令常量类\n"]

    for category, content in commands.items():
        class_name = category.capitalize()
        desc = content.get("description", "")
        lines.append(f"class {class_name}:")
        if desc:
            lines.append(f'    """{desc}"""\n')

        groups = content.get("groups", {})
        for group, actions in groups.items():
            sub_class_name = group.capitalize()
            lines.append(f"    class {sub_class_name}:")
            for action, cmd in actions.items():
                const_name = action.upper()
                lines.append(f'        {const_name} = "{cmd}"')
            lines.append("")
        lines.append("")

    with open(output_file, "w", encoding="utf-8") as f:
        f.write("\n".join(lines))
    print(f"✅ Python 类文件已生成: {output_file}")


if __name__ == "__main__":
    yaml_file = "visa_commands.yaml"
    with open(yaml_file, "r", encoding="utf-8") as f:
        commands = yaml.safe_load(f)
    print(commands)

    # generate_markdown(commands, "visa_commands.md")
    # generate_html("visa_commands.md", "visa_commands.html")
    out_file = os.path.join(os.getcwd(), 'visa_lib', 'visa_commands.py')
    generate_python_class(commands, out_file)
