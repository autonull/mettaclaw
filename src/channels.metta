;Embodiment abstraction - supports multiple channels
;Channel configuration (set via environment or config):
(= (commchannel) (empty))
(= (IRC_channel) (empty))
(= (IRC_server) (empty))
(= (IRC_port) (empty))
(= (IRC_user) (empty))
(= (CLI_prompt) (empty))

;Initialize channels based on configuration
(= (start_channel irc)
   (progn
     (configure IRC_channel (py-call (os.environ.get "IRC_CHANNEL" "##metta")))
     (configure IRC_server (py-call (os.environ.get "IRC_SERVER" "irc.libera.chat")))
     (configure IRC_port (py-call (os.environ.get "IRC_PORT" "6667")))
     (configure IRC_user "mettaclaw")
     (py-call (channels.embodiment.start_irc (IRC_channel) (IRC_server) (IRC_port) (IRC_user)))))

(= (start_channel cli)
   (progn
     (configure CLI_prompt "> ")
     (py-call (channels.embodiment.start_cli (CLI_prompt) "MeTTaClaw CLI - type to interact"))))

(= (start_channel mattermost)
   (py-call (channels.embodiment.start_mattermost "https://chat.example.com" "channel" "token")))

(= (start_channel $unknown)
   (println! ("Unknown channel type: " $unknown)))

(= (initChannels)
 (progn (println! "Initializing channels")
   (let $chan (py-call (os.environ.get "METTACLAW_CHANNEL" "irc"))
     (progn
       (configure commchannel $chan)
       (start_channel (commchannel))))))

;Receive message from any active channel
(= (receive)
 (py-call (channels.embodiment.receive_all)))

;Send message to all active channels
(= (send $msg)
 (if (!= $msg (get-state &lastsend))
     (progn
       (change-state! &lastsend $msg)
       (let $safemsg (string-replace (string-replace $msg "_" " ") "\n" "\\n")
         (py-call (channels.embodiment.send_all $safemsg))))
     _))

;Send to specific channel
(= (send-to $channel $msg)
 (py-call (channels.embodiment.send_to $channel $msg)))

;Get list of active channels
(= (list-channels)
 (py-call (channels.embodiment.get_active_channels)))

;Search the internet
(= (search $msg)
 (py-call (websearch.search $msg)))
