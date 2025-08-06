from jinja2 import Environment, FileSystemLoader

class TemplateRenderer:
    def __init__(self, template_dir: str):
        self.env = Environment(loader=FileSystemLoader(template_dir))

    def render(self, template_name: str, context: dict) -> str:
        template = self.env.get_template(template_name)
        return template.render(context)
    
    ##############################################################
    # RENDER TEMPLATES
    ##############################################################
    def render_approver_request_template(self, context: dict) -> str:
        return self.render("approver_new_request.html", context)
    
    def render_requester_request_template(self, context: dict) -> str:
        return self.render("requester_new_request.html", context)
    
    def render_comment_template(self, context: dict) -> str:
        return self.render("requesters_comment_template.html", context)
    
    def render_requester_approved_template(self, context: dict) -> str:
        return self.render("requester_approved_request.html", context)
