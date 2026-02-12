\documentclass[11pt]{article}
\usepackage{amsmath}
\usepackage{amsfonts}
\usepackage{amsthm}
\usepackage[utf8]{inputenc}
\usepackage[margin=0.75in]{geometry}


\title{CSC111 Winter 2026 Project 1}
\author{Nicolas Miranda Cantanhede; Cade McNelly}
\date{\today}

\begin{document}
\maketitle

\section*{Running the game}

You can run the game in two different ways:
\begin{itemize}
    \item Terminal: You should be able to run the game by simply running \texttt{adventure.py}.
    \item Game with visuals (Enhancement): You should run \texttt{ui.py}. Please, to make sure everything runs smoothly, check if you have \texttt{pygame} and all the regular CSC111 libraries installed.
\end{itemize}

\section*{Game Map}

\begin{verbatim}
-1 -1  7  8 -1 -1 32 15 -1 -1 -1
-1 -1  6 -1 -1 -1 14 16 17 -1 -1
 5  4  3  2  1 -1 13 -1 18 19 -1
-1 -1 -1 -1  9 10 11 12 -1 20 21
24 23 22 -1 -1 -1 31 -1 -1 33 25
-1 -1 26 27 28 30 29 -1 -1 -1 -1
-1 -1 -1 -1 34 -1 -1 -1 -1 -1 -1
\end{verbatim}

Starting location is: 2 \\

Overall list of commands: \\

go north \qquad go south \qquad go east \qquad go west \qquad look \qquad inventory \qquad log \qquad quit \\[6pt]
\hphantom{--------}take $<\text{item}>$ \qquad drop $<\text{item}>$ \qquad inspect $<\text{item}>$ \qquad submit early \qquad score

\section*{Game solution} \\

Players can win if they perform the following commands (in chronological order):
\begin{verbatim}
["take tcard", "go west", "take signed extension request", "go west", "take dorm key",
"go west", "take lucky mug", "go east", "go east", "go east", "go east", "go south", "go east",
"go east", "go east", "take usb drive", "go west", "go north", "go north", "go east", "go east",
"go south", "go east", "take toonie","go west", "go north", "go west", "go west", "go south",
"go south", "go south", "go south", "go west", "go west", "go west", "drop toonie", "go east",
"go east", "go east", "go north", "go north", "go north", "go north", "go east", "go east",
"go south", "go east", "go south", "go south", "drop coffee", "go north", "go east",
"take laptop charger", "go west", "go north", "go west", "go north", "go west", "go west",
"go south",  "go south", "go west", "go west", "go north", "drop lucky mug", "drop usb drive",
"drop laptop charger", "submit early"]
\end{verbatim}

Fun fact: this is also the most optimal way we have found to win the game.

\section*{Lose condition(s)} \\
\textbf{Lose Condition 1:}
Players ultimately lose if they use up all the maximum number of moves. The default number is \textbf{67}, but we tried to make that a bit more dynamic through an extension that allows you to get extra moves. If you ran out of moves, the game ends with a game-over message. \\ \textbf{Lose Condition 2:} Using submit early immediately ends the run. Submit early is only a loss if win requirements are not met. \\


List of commands for condition 1: From the lose demo in \texttt{simulation.py}, the command sequence is: \\


\hphantom{---------------------------} ["go west", "go east"] * 33 + ["go west"] \qquad (67 moves)\\

List of commands for condition 2: \\


\hphantom{------------------------------------------------------} ["submit early"] \\

Parts of code are involved in this functionality:
    \begin{verbatim}
    adventure.py:
        - DEFAULT_MAX_TURNS, PlayerState.max_turns, AdventureGame.turn
        - AdventureGame.submit_early()
        - AdventureGame.has_required_returns(), AdventureGame.has_storage_solution()
        - AdventureGame.apply_location_rewards() for +30 move extension
    ui.py:
        - GameUI.do_move() increments turns
        - GameUI.do_submit() triggers early submission
        - GameUI._resolve_end_state() decides win/lose
    \end{verbatim}

% Copy-paste the above if you have multiple lose conditions and describe each possible way to lose the game

\section*{Inventory}

\begin{enumerate}
\item All location IDs in the game that contains items themselves and/or have functionalities related to items:
\begin{verbatim}
    1, 2, 3, 4, 5, 6, 7, 9, 10, 11, 12, 13, 14, 15, 16, 17,
    18, 19, 20, 21, 22, 23, 24, 25, 27, 28, 29, 30, 32, 33, 34
\end{verbatim}

\item Item data (name: start location $\rightarrow$ target location):
\begin{verbatim}
    usb drive: 12 -> 1                    laptop charger: 21 -> 1
    lucky mug: 5 -> 1                     tcard: 2 -> 1
    stapler: 29 -> 29                     campus map: 6 -> 6
    gym pass: 6 -> 6                      bus ticket: 7 -> 7
    umbrella: 9 -> 9                      protein bar: 9 -> 12
    sticky notes: 10 -> 33                study timer: 11 -> 12
    lecture notes: 13 -> 33               clicker: 14 -> 14
    camera strap: 3 -> 34                 hand sanitizer: 16 -> 24
    notebook: 1 -> 33                     scarf: 17 -> 7
    spare usb cable: 18 -> 1              toonie: 19 -> 27
    python cheat sheet: 20 -> 33          pencil: 15 -> 29
    flashcard deck: 23 -> 33              printed report: 25 -> 32
    blue pen: 22 -> 32                    coffee: 27 -> 33
    headphones: 28 -> 12                  cookie: 2 -> 33
    water bottle: 28 -> 12                sticker sheet: 29 -> 33
    spare paper: 25 -> 25                 calculator: 30 -> 12
    lab access form: 33 -> 32             marker: 30 -> 21
    dorm key: 4 -> 3                      office hours token: 28 -> 33
    assignment cover sheet: 29 -> 32      signed extension request: 3 -> 32
    library book: 12 -> 24                group meeting notes: 23 -> 33
    lost-and-found tag: 15 -> 34
\end{verbatim}

\item Exact command(s) that should be used to pick up an item (choose any one or more items for this example), and the command(s) used to use/drop the item (can copy the list you assigned to
\texttt{inventory\_demo} in the \texttt{simulation.py} file)

\begin{verbatim}
go west -> go west -> take dorm key -> go east -> drop dorm key -> inventory
\end{verbatim}

\item Which parts of your code (file, class, function/method) are involved in handling the \texttt{inventory} command:
\begin{verbatim}
adventure.py:
- AdventureGame.inventory (property)
- AdventureGame.pick_up(), AdventureGame.drop(),
  AdventureGame.get_item(), AdventureGame.inspect()

ui.py:
- GameUI.open_take_modal(), GameUI.open_drop_modal(),
  GameUI.open_inspect_modal(), GameUI.do_inventory()
\end{verbatim}
\end{enumerate}

\section*{Score}
\begin{enumerate}

    \item How scoring works, first score increase location, and command path:

Players earn score when dropping items at their target location. Points are read from each item's
\texttt{target\_points} in \texttt{game\_data.json}. The three main objective items (USB drive, laptop charger,
lucky mug) are each worth 30 points. Optional side tasks add smaller points. \\

Special rule: \texttt{spare usb cable} can substitute for \texttt{usb drive}; if USB drive was not returned yet,
dropping spare USB cable can award the USB-drive value.

In our score demo, the first score increase happens at \textbf{Location 1 (Dorm Room)} by dropping the USB drive:
\begin{verbatim}
[take tcard, go west, go west, take dorm key, go east, go east, go east,
 go south, go east, go east, go east, take usb drive,
 go west, go west, go west, go north, drop usb drive, score]
\end{verbatim}

\item \texttt{scores\_demo} list from \texttt{simulation.py}:
\begin{verbatim}
["take tcard",
"go west", "go west", "take dorm key", "go east", "go east", "go east",
"go south", "go east", "go east", "go east", "take usb drive",
"go west", "go west", "go west", "go north", "drop usb drive", "score"]
\end{verbatim}

\item Parts of the code (file, class, function/method) involved in handling the \texttt{score} functionality:
\begin{verbatim}
adventure.py:
- AdventureGame.score (property)
- AdventureGame.check_quest() (awards points on correct drop)
- AdventureGame.has_required_returns(), AdventureGame.has_storage_solution()
- AdventureGame.lock_score() (score freeze after post-win explore mode)

ui.py:
- GameUI.do_score() (prints score + percentage)
- GameUI._draw_header() (shows score in UI chip)

ui_endscreen.py:
- EndScreenView._summary_lines() (shows final project grade percentage)
\end{verbatim}

\end{enumerate}

\section*{Enhancements}
\begin{enumerate}
    \item Enhancement 1: Game Visuals
    \begin{itemize}
        \item This is something we developed to deeepen our understanding of \texttt{pygame}. It is basically a UI that imitates ACORN style and has all the logic of the terminal version but with a working mini-map + clickable actions.
        \item Complexity level: High
        \item Why: We spent most of the actual project in this implementation, with around 1500 extra lines of code and three extra file specifically for it (see \texttt{ui.py, ui\_endscreen.py, and ui.\_primitives.py}). The main challenges we had were:
        \begin{itemize}
            \item MiniMap: We had a hard time making the directions consistent. In some cases, moving west would appear in the minimap as moving south. To fix this, we redesigned the map connections to use a simpler linear layout, which ended up working better.
            \item Scrolling UI: Scrolling was way more annoying than we thought. The wheel would scroll the wrong direction and sometimes the action buttons would spill outside the panel. We had to give each subpanel its own scroll area so only the section the user is hovering scrolls and stay contained.
        \end{itemize}
        \item Parts of the code which are involved in this enhancement: \texttt{ui.py, ui\_endscreen.py, and ui\_primitives.py}
        \item Demo commands (\texttt{enhancement1\_demo} in \texttt{simulation.py}):
        \begin{verbatim}
        ["take tcard", "go west", "take signed extension request",
        "go west", "take dorm key", "go east", "go east", "go east", "go south",
        "go east", "go east","go north", "go north", "go north",
        "drop signed extension request"]
        \end{verbatim}
    \end{itemize}


   \item Enhancement \#2: Puzzle progression + time extension
\begin{itemize}
    \item Brief description: In a nutshell, we added  an item-gated puzzle chain and extra moves:
    \begin{itemize}
        \item Dorm Room access is locked behind \texttt{dorm key}.
        \item Bahen 2F Labs access is locked behind \texttt{lab access form}.
        \item \texttt{toonie} can be traded for \texttt{coffee} at Cafe Alley.
        \item \texttt{coffee} can be traded for \texttt{lab access form} at TA Help Table.
        \item Submitting \texttt{signed extension request} at Professor's Office grants +30 moves once.
    \end{itemize}

    \item Complexity level: High

    \item Why:
    It combines location restrictions, item-trade rewards, and a bonuses system. Therefore, it adds a layer of logic that makes the game itself more dynamic and complex. Its definitely less robust than Enhancement \#1 in terms of extra code, but it is considerably impactful and extensive to the gameplay

    \item Code involved:
    \texttt{game\_data.json} (restrictions/rewards),
    \texttt{adventure.py} (\texttt{can\_enter\_location}, \texttt{apply\_location\_rewards}, \texttt{\_apply\_item\_reward}),
    \texttt{simulation.py} (demo sequences),
    \texttt{ui.py} (move + drop flow through visual commands).

    \item Demo commands (excerpt shown in \texttt{win\_walkthrough}/\texttt{enhancement1\_demo}):
\begin{verbatim}
take toonie -> drop toonie (at Cafe Alley) -> drop coffee (at TA Help Table)
take lab access form -> enter Bahen 2F Labs -> take laptop charger
drop signed extension request (at Professor's Office) -> +30 moves
\end{verbatim}
\end{itemize}
\end{enumerate}


\end{document}
