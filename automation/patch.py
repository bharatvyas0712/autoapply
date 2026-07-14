import sys

with open('form_filler.py', 'r', encoding='utf-8') as f:
    lines = f.readlines()

new_lines = []
in_resolve = False
for line in lines:
    if line.startswith('def _resolve_via_review_queue(page'):
        pause_func = '''def pause_for_user_input(page, prompt_text="Please answer the question on screen"):
    try:
        page.evaluate(f"""() => {{
            const btn = document.createElement('button');
            btn.id = 'autojobapply-resume-btn';
            btn.innerHTML = 'Resume Automation ➔';
            btn.style.position = 'fixed';
            btn.style.bottom = '20px';
            btn.style.right = '20px';
            btn.style.zIndex = '999999';
            btn.style.padding = '15px 25px';
            btn.style.fontSize = '18px';
            btn.style.fontWeight = 'bold';
            btn.style.backgroundColor = '#0066cc';
            btn.style.color = 'white';
            btn.style.border = 'none';
            btn.style.borderRadius = '8px';
            btn.style.cursor = 'pointer';
            btn.style.boxShadow = '0 4px 12px rgba(0,0,0,0.3)';
            
            const label = document.createElement('div');
            label.id = 'autojobapply-prompt-label';
            label.innerText = `{prompt_text}`;
            label.style.position = 'fixed';
            label.style.bottom = '80px';
            label.style.right = '20px';
            label.style.zIndex = '999999';
            label.style.backgroundColor = '#fff3cd';
            label.style.color = '#856404';
            label.style.padding = '10px 15px';
            label.style.border = '2px solid #ffeeba';
            label.style.borderRadius = '8px';
            label.style.fontWeight = 'bold';
            label.style.maxWidth = '300px';
            
            btn.onclick = () => {{
                btn.remove();
                label.remove();
            }};
            document.body.appendChild(label);
            document.body.appendChild(btn);
        }}""")
        page.wait_for_function("!document.getElementById('autojobapply-resume-btn')", timeout=0)
    except Exception as e:
        pass

'''
        new_lines.append(pause_func)
        new_lines.append(line)
        in_resolve = True
    elif in_resolve and 'leaving blank and continuing' in line:
        new_lines.append('            add_log(f"  🤖 AI could not answer \'{question_text[:60]}\'. Pausing for your manual input...", "warn")\n')
        new_lines.append('            pause_for_user_input(page, f"AI couldn\'t answer:\\n\\n{question_text[:100]}\\n\\nPlease answer manually and click Resume.")\n')
    elif in_resolve and 'leaving blank' in line and 'warn' in line:
        new_lines.append('        add_log(f"  No profile data to answer \'{question_text[:60]}\'. Pausing for your manual input...", "warn")\n')
        new_lines.append('        pause_for_user_input(page, f"No profile data to answer:\\n\\n{question_text[:100]}\\n\\nPlease answer manually and click Resume.")\n')
    elif in_resolve and line.startswith('def try_select_option'):
        in_resolve = False
        new_lines.append(line)
    else:
        new_lines.append(line)

with open('form_filler.py', 'w', encoding='utf-8') as f:
    f.writelines(new_lines)
print('Done!')
