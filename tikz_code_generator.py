class TikzCodeGenerator:
    def __init__(self, state_manager, transition_manager):
        self.state_manager = state_manager
        self.transition_manager = transition_manager

    def generate_code(self):
        tikz_code = ["\\begin{tikzpicture}[->,>=stealth',shorten >=1pt,auto,node distance=2.8cm,semithick]"]
        for state_id, state_info in self.state_manager.states.items():
            position = f"({state_info['position'][0]/100},{-state_info['position'][1]/100})"
            label = state_info['label']
            tikz_code.append(f"\\node[state] (S{state_id}) {position} {{$label$}};")
        for transition in self.transition_manager.transitions:
            start_state = 'S' + str(transition['start'])
            end_state = 'S' + str(transition['end'])
            label = transition['label']
            if transition['type'] == 'curved_transition':
                control = transition['control']
                tikz_code.append(f"\\draw (S{start_state}) to[out=45,in=225,looseness=1.5] node {{$label$}} (S{end_state});")
            else:
                tikz_code.append(f"\\path (S{start_state}) edge node {{$label$}} (S{end_state});")
        tikz_code.append("\\end{tikzpicture}")
        return "\n".join(tikz_code)
