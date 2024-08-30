#!/usr/bin/env python3
import sys
import termios
import tty
import random
import time
import select

key_mapping = {
    "[A": "up",
    "[B": "down",
    "[C": "right",
    "[D": "left",
    "2A": "shift+up",
    "2B": "shift+down",
    "2C": "shift+right",
    "2D": "shift+left",
    "5A": "ctrl+up",
    "5B": "ctrl+down",
    "5C": "ctrl+right",
    "5D": "ctrl+left",
    "\x17": "C-w",
    "\x0f": "C-o",
    "\x03": "C-c",
    "\x07": "C-g",
}


def get_key(key_previous=None):
    fd = sys.stdin.fileno()
    old_settings = termios.tcgetattr(fd)
    special_char = "\x1b"
    if key_previous is None:
        key_previous = special_char
    try:
        tty.setraw(fd)
        key = sys.stdin.read(1)
        if key in key_mapping:
            return key_mapping[key]
        if key == "[":
            key += sys.stdin.read(1)
            if key in key_mapping:
                return key_mapping.get(key, key)
            if key[-1] == "1":  # shift plus special key
                if sys.stdin.read(1) == ";":  # ;followed by key
                    key = sys.stdin.read(2)
                    return key_mapping.get(key, key)
                if key == special_char:
                    time.sleep(0.1)
                    if sys.stdin in select.select([sys.stdin], [], [], 0)[0]:
                        key += sys.stdin.read(2)
                    key = key_mapping.get(key, key)

    finally:
        termios.tcsetattr(fd, termios.TCSADRAIN, old_settings)

    return key


def clear_terminal():
    sys.stdout.write("\033[2J")
    # Move cursor
    sys.stdout.write("\033[H")
    sys.stdout.flush()


class Randoms:
    # select next ten characters and replace ' with "
    input_choices = list("abcdefghijklmnopqrstuvwxyz")
    word_choices = word_list = [
        "apple",
        "banana",
        "cherry",
        "date",
        "elderberry",
        "fig",
        "grape",
        "honeydew",
        "kiwi",
        "lemon",
        "mango",
        "nectarine",
        "orange",
        "pear",
        "quince",
        "raspberry",
        "strawberry",
        "tangerine",
        "ugli",
        "vaccine",
        "watermelon",
        "xigua",
        "yam",
        "zucchini",
    ]

    def __init__(self):
        self.replace = {}
        self.replace["<randc1>"] = random.choice(self.input_choices)
        self.replace["<randc2>"] = random.choice(self.input_choices)
        self.replace["<randc3>"] = random.choice(self.input_choices)
        self.replace["<rints1>"] = random.randint(2, 5)
        self.replace["<rints2>"] = random.randint(2, 5)
        self.replace["<rints3>"] = random.randint(2, 5)
        self.replace["<w1>"] = random.choice(self.word_choices)
        self.replace["<w2>"] = random.choice(self.word_choices)
        self.replace["<w3>"] = random.choice(self.word_choices)

    def apply(self, task):
        task.question = task.base_question
        task.keyboard_input = task.base_keyboard_input
        for key, value in self.replace.items():
            task.question = task.question.replace(key, str(value))
            task.keyboard_input = task.keyboard_input.replace(
                key, ",".join(list(str(value)))
            )
        task.applied_random = (
            task.question != task.base_question
            or task.keyboard_input != task.base_keyboard_input
        )


class Task:

    questions_total = 0

    def __init__(self, question, keyboard_input):
        Task.questions_total += 1
        self.question_number = Task.questions_total
        self.base_question = question
        self.base_keyboard_input = keyboard_input
        self.question = question
        self.keyboard_input = keyboard_input
        self.success = False
        self.tasks = []
        self.applied_random = False
        self.first_time_executed = True
        r = Randoms()
        r.apply(self)

    def add_task(self, task):
        self.tasks.append(task)

    def execute(self):
        if not self.first_time_executed:
            r = Randoms()
            r.apply(self)
        self.first_time_executed = False
        print("{}".format(self.question))
        index = 0
        mistake = False
        key_previous = None
        for expected in self.keyboard_input.split(","):
            key = get_key(key_previous)
            key_previous = key
            if key == "\x1b":
                key = get_key(key_previous)
                key_previous = key
            if key == "C-c":
                raise KeyboardInterrupt()
            if key == "\x17":
                print("CTRL+W")
            else:
                print(key, end="", flush=True)
            if expected == key:
                index += 1
            else:
                mistake = True

            if mistake:
                print('\n"{}" is incorrect.'.format(repr(key)))
                print(
                    '\nExpected input: "{}".'.format(
                        self.keyboard_input.replace(",", "")
                    )
                )
                print("\nPress any key to continue...")
                get_key(None)
                break
            if key == "q":
                break
        if not mistake:
            self.success = True
            print("")
            print(
                random.choice(
                    ["Great!", "Excelent!", "Awesome!", "Keep it up!", "Perfect!"]
                )
            )
            print("")
            self.success = all([task.execute() for task in self.tasks])
            time.sleep(0.40)
        return self.success


tasks = [
    Task("Open terminal\n", ":,terminal,\r"),
    Task("Delete from the cursor to the end of the word.", "d,e"),
    Task("Delete from the cursor to the end of the line.", "d,$"),
    Task("Delete from the cursor to the beginning of the next word.", "d,w"),
    Task("Delete <rints1> lines using a numeric value.", "<rints1>,d,d"),
    Task("Move backward in the search results.", "N"),
    Task("Move forward in the search results.", "n"),
    Task("Move to line number <rints1>.", "<rints1>,G"),
    Task("Undo all changes on the current line.", "U"),
    Task("Move to the end of the word.", "e"),
    Task("Move to the beginning of the line.", "0"),
    Task("Search backward for <w1>.", ":,?,<w1>,\r"),
    Task("Search forward for <w1>.", ":,/,<w1>,\r"),
    Task("Display the current location in the status bar.", "C-g"),
    Task("Indent the selected text.", ">,>"),
    Task("De-indent the selected text.", "<,<"),
    Task("Save the document as <w1>.py.", ":,w, ,<w1>,.,p,y,\r"),
    Task("Replace the first occurrence of <w1> with <w2>.", ":,s,/,<w1>,/,<w2>,/,g"),
    Task(
        "Replace all occurrences of <w1> with <w2> in the entire file.",
        ":,%,s,/,<w1>,/,<w2>,/,g",
    ),
    Task(
        "Replace all occurrences of <w1> with <w2> in the entire file, with confirmation for each change.",
        ":,%,s,/,<w1>,/,<w2>,/,g,c",
    ),
    Task(
        "Select the next five characters and save them to a file.",
        "v,right,right,right,right,:,w",
    ),
    Task("Exit Vim.", ":,q"),
    Task("Split the screen vertically.", ":,v,s,p,l,i,t,\r"),
    Task("Split the screen horizontally.", ":,s,p,l,i,t,\r"),
    Task("Merge the file <w1>.txt into the current file.", ":,r, ,<w1>,.,t,x,t,\r"),
    Task(
        "Move three words to the left without using numeric values.",
        "ctrl+left,ctrl+left,ctrl+left",
    ),
    Task(
        "Move three words to the right without using numeric values.",
        "ctrl+right,ctrl+right,ctrl+right",
    ),
    Task("Return to the previous position.", "C-o"),
    Task("Type <w1>.", "<w1>"),
    Task("Indent the current line and the two lines below.", "v,down,down,>,>"),
    Task("Enable case-sensitive search.", ":,s,e,t, ,n,o,i,c"),
    Task("Enable case-insensitive search.", ":,s,e,t, ,i,c"),
    Task("Copy the word under the cursor.", "y,w"),
    Task("Replace the text under the cursor with <w1>.", "R,<w1>"),
    Task("Insert text at the end of the line.", "A"),
    Task("Insert text after the cursor.", "a"),
    Task("Insert a new line below the current line.", "o"),
    Task("Insert a new line above the current line.", "O"),
    Task("Move to the beginning of the document.", "g,g"),
    Task("Move to the end of the line.", "$"),
    Task("Move to the end of the document.", "G"),
    Task(
        "Select the next four characters and copy them.", "v,right,right,right,right,y"
    ),
    Task("Switch to the next window.", "C-w,C-w"),
    Task("Swap the position of the current window with another.", "C-w,r"),
    Task("Copy the current line.", "y,y"),
    Task("Copy all content.", "y"),
    Task("Paste the copied content.", "p"),
    Task("Replace the character under the cursor with '<randc1>'.", "r,<randc1>"),
    Task("Delete the character under the cursor.", "x"),
    Task("Delete the line under the cursor.", "d,d"),
    Task("Cut the current line.", "c,c"),
    Task("Type <w1>.", "<w1>"),
]


# shift select Move with>>
def main():
    questions_correct = []
    questions_incorrect = []
    question_count = 0
    durations = []
    while tasks:
        clear_terminal()
        if not durations:
            avg_reaction_time = 0
        else:
            avg_reaction_time = sum(durations) / len(durations)
        num_correct = len(questions_correct)
        num_incorrect = len(questions_incorrect)
        avg_time = round(sum(durations) / len(durations), 2) if durations else 0
        print(
            "Correct: {}\tIncorrect: {}\tAvg reaction time: {}".format(
                num_correct, num_incorrect, avg_time
            )
        )
        print("")
        question_count += 1
        task = random.choice(tasks)
        print("{}. ".format(question_count), end="")
        time_start = time.time()
        if task.execute():
            tasks.remove(task)
            questions_correct.append(task)
        else:
            questions_incorrect.append(task)
        time_end = time.time()
        durations.append(time_end - time_start)


# tasks.remove(task)


if __name__ == "__main__":
    main()
