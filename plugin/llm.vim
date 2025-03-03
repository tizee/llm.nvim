" llm.vim - Vim plugin to interact with LLM models

" Check for uv availability first
let s:has_uv = executable('uv')

" Fallback to Python3 if uv not available
let py3 = get(g:,'python3_host_prog')
if !s:has_uv && len(py3) == 0
  echoerr "Either uv or Python3 is required for llm.vim"
  finish
endif

command! -nargs=* LLM call LLM#RunLLM(<q-args>)
vnoremap <leader>? :<C-u>call LLM#SendSelectionAsPrompt()<CR>
xnoremap <leader>? :<C-u>call LLM#SendSelectionAsPrompt()<CR>
