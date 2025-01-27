" set ff=unix
" autoload/llm.vim

let s:plugin_root = expand('<sfile>:p:h:h')

function! LLM#RunLLM(prompt) abort
    " Get config, keys, logs path, system prompt and model name from global variables
    let config_path = get(g:, 'llm_config_path', expand('$HOME/.config/llm/llm.vim.yaml'))
    let keys_path = get(g:, 'llm_api_keys_path', expand('$HOME/.config/llm/keys.json'))
    let logs_path = get(g:, 'llm_logs_path', expand('$HOME/.config/llm/llm_logs.db'))
    let system_prompt = get(g:, 'llm_system_prompt', '')
    let model_name = get(g:, 'llm_model_name', '')
    echom "model name:". model_name

    " Set the path of the LLM CLI script
    let llm_cli_path = s:plugin_root
    let llm_cli_path.= has("win32")? '\llm.py' : '/llm.py'

    " Capture the output line by line
    let model_hint = model_name. ' > '
    " Get the current cursor position (line and column)
    let [current_line, current_col] = getpos('.')[1:2]

    " Move the cursor to the target line
    call append(current_line, model_hint)
    call append(current_line, '')
    call cursor(current_line + 2, 1)

    let last_line = line('$')
    " Add empty lines if the final line is out of range
    let final_line = current_line + 4
    while final_line > last_line
        call append(line('$'), '')
        let last_line = last_line + 1
    endwhile

    " Move the cursor to the final line
    call cursor(final_line, 1)

    " Variables for shell command and args
    let shell_cmd = get(g:,'python3_host_prog','python3')
    " enforce unbuffered output
    let shell_args = '-u'

    " Start a job to run the LLM CLI script
    call jobstart([shell_cmd, shell_args, llm_cli_path, 'model', '-m', model_name, '--db-path', logs_path, '--config', config_path, '--api-keys', keys_path, '--system-prompt', system_prompt, a:prompt], {
                \ 'on_stdout': {j,d,e->s:HandleStream(j,d,e)},
                \ 'on_stderr': {j,d,e->s:HandleError(j,d,e)},
                \ 'stdout_buffered': v:false })
endfunction

function s:HandleError(_, data, event) abort
    " Only handle stderr events
    if a:event!= "stderr"
        return
    endif
    " Echo error message if data is not empty
    if len(a:data) > 1
        let output = string(a:data)
        echom 'Error: '. output
    endif
endfunction

function s:HandleStream(_, data, event) abort
    " Only handle stdout events
    if a:event!= "stdout"
        return
    endif

    " Ensure there is enough space below the current line
    let [current_line, current_col] = getpos('.')[1:2]
    let last_line = line('$')
    if current_line == last_line
        call append(last_line, '')
    endif

    " Iterate over each line of received data
    for parts in a:data
        let line = split(parts, '\r\?\n', 1)
        " Iterate over each character in the line
        for char in line
            " Append character to the current line
            let current_text = getline('.')
            let new_text = current_text. char
            call setline(line('.'), new_text)
            call cursor(line('.'), len(new_text))
            " Move to the next line if this part ends with a line break
            if char == ''
              if line('.') == line('$')
                  call append(line('$'), '')
              endif
              call cursor(line('.') + 1, 1)
            endif
        endfor
    endfor

    redraw
endfunction

function! LLM#SendSelectionAsPrompt() range abort
    " Get the selected text using the range
    let prompt = join(getline(a:firstline, a:lastline), "\n")

    " Run the LLM with the selected text as prompt
    call LLM#RunLLM(prompt)
endfunction
