" llm.vim - Vim plugin to interact with LLM models
if !has('python3')
  echoerr "Python3 is required for llm.vim"
  finish
endif

command! -nargs=* LLM call LLM#RunLLM(<q-args>)
vnoremap <leader>? :<C-u>call LLM#SendSelectionAsPrompt()<CR>
xnoremap <leader>? :<C-u>call LLM#SendSelectionAsPrompt()<CR>
