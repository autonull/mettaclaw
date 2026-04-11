;Configured at runtime memory and history in amount of characters:
(= (maxFeedback) (empty))
(= (maxRecallItems) (empty))
(= (maxEpisodeRecallLines) (empty))
(= (maxHistory) (empty))
(= (maxErrorFeedback) (empty))

(= (initMemory)
   (progn (println! "Initializing memory")
          (configure maxFeedback 5000)
          (configure maxRecallItems 20)
          (configure maxEpisodeRecallLines 20)
          (configure maxHistory 8000)
          (configure maxErrorFeedback 2000)))

(= (getPrompt)
   (read-file (library mettaclaw ./memory/prompt.txt)))

(= (getHistory)
   (let $ret (read-file (library mettaclaw ./memory/history.metta))
        (let $clean (py-call (helper.clean_response $ret))
             (last_chars $clean (maxHistory)))))

(= (addToHistory $lastmessage $response $sexpr $msgnew)
   (let* (($clean (py-call (helper.clean_response $response)))
          ($human_str (if $msgnew (py-call (helper.normalize_string ("HUMAN_MESSAGE: " $lastmessage (newline)))) ""))
          ($error_state (get-state &error))
          ($err_str (if (== $error_state ()) ""
                        (py-call (helper.normalize_string (" ERROR: " (last_chars (string-safe (repr $error_state)) (maxErrorFeedback))))))))
         (appendToHistory ((get_time_as_string) (newline) $human_str $clean (newline) $err_str))))

(= (appendToHistory $addition)
   (let $raw (swrite $addition)
        (let $clean (py-call (helper.clean_response $raw))
             (append-file (library mettaclaw ./memory/history.metta) $clean))))

(= (remember $str)
   (py-call (lib_llm_ext.remember $str (get_time_as_string))))

(= (query $str)
   (let $raw (py-call (lib_llm_ext.query_memories $str (maxRecallItems)))
        (if (== $raw true)
            (py-str ("No memories found for: " $str))
            $raw)))

(= (episodes $time)
   (py-call (helper.around_time $time (maxEpisodeRecallLines))))
