import requests
import html
import random
import threading
import queue
import time
import sys

CATEGORY_URL = "https://opentdb.com/api_category.php"
QUESTION_URL = "https://opentdb.com/api.php"
TIME_LIMIT = 15  # seconds per question

# ------------------ API functions ------------------

def fetch_categories():
    resource = requests.get(CATEGORY_URL)
    data = resource.json()
    return data["trivia_categories"]

def fetch_questions(amount=10, difficulty=None, category=None, qtype=None):
    needs = {"amount": amount}
    if difficulty:
        needs["difficulty"] = difficulty
    if category:
        needs["category"] = category
    if qtype:
        needs["type"] = qtype
    resource = requests.get(QUESTION_URL, params=needs)
    data = resource.json()
    return data.get("results", [])

# ------------------ user input selection ------------------

def select_category(categories):
    print("Select a category:")
    for i, cat in enumerate(categories, 1):
        print(i, cat["name"])
    choice = int(input("Enter your choice: "))
    if 1 <= choice <= len(categories):
        return categories[choice - 1]["id"]
    return None

def select_difficulty():
    difficulties = ["easy", "medium", "hard"]
    print("Select difficulty: ")
    for i, diff in enumerate(difficulties, 1):
        print(i, diff)
    choice = int(input("Enter number: "))
    if 1 <= choice <= len(difficulties):
        return difficulties[choice - 1]
    return None

def select_question_type():
    types = [("multiple", "Multiple Choice"), ("boolean", "True/False")]
    print("Select question type:")
    for i, name in enumerate(types, 1):
        print(i, name[1])
    choice = input("Enter number (or press Enter for Any): ").strip()
    if choice.isdigit() and 1 <= int(choice) <= len(types):
        return types[int(choice) - 1][0]
    return None

# ------------------ Input Thread with Timer ------------------

class InputThread(threading.Thread):
    def __init__(self, prompt, q):
        super().__init__(daemon=True)
        self.prompt = prompt
        self.q = q

    def run(self):
        try:
            ans = input(self.prompt)
            self.q.put(ans)
        except Exception:
            self.q.put(None)

# ------------------ quiz logic ------------------

def ask_question(question_data):
    question = html.unescape(question_data["question"])
    correct_answer = html.unescape(question_data["correct_answer"])
    options = [html.unescape(opt) for opt in question_data["incorrect_answers"]]
    options.append(correct_answer)
    random.shuffle(options)

    print("\nQuestion:")
    print(question)
    for i, option in enumerate(options, 1):
        print(i, option)

    q = queue.Queue()
    it = InputThread("\nEnter your choice (number): ", q)
    it.start()

    start = time.time()
    while True:
        elapsed = time.time() - start
        remaining = TIME_LIMIT - elapsed
        if remaining <= 0:
            break

        sys.stdout.write(f"\rTime left: {int(remaining)}s ")
        sys.stdout.flush()

        try:
            ans = q.get_nowait()
            if ans and ans.isdigit() and 1 <= int(ans) <= len(options):
                chosen = options[int(ans) - 1]
                sys.stdout.write("\r" + " " * 30 + "\r")
                if chosen == correct_answer:
                    print("✅ Correct!\n")
                    return True
                else:
                    print(f"❌ Incorrect. Correct answer was: {correct_answer}\n")
                    return False
            else:
                print("\nInvalid input.")
                return False
        except queue.Empty:
            time.sleep(0.1)
            continue

    # Time ran out
    sys.stdout.write("\r" + " " * 30 + "\r")
    print("⏰ Time's up! No answer given.")
    print(f"Correct answer was: {correct_answer}\n")
    return False

def select_quiz_options(categories):
    category = select_category(categories)
    difficulty = select_difficulty()
    qtype = select_question_type()
    questions = fetch_questions(amount=5, category=category, difficulty=difficulty, qtype=qtype)
    return questions

# ------------------ main function ------------------

def main():
    print("Welcome to TimeTickQuiz!")
    categories = fetch_categories()
    questions = select_quiz_options(categories)
    score = 0
    for q in questions:
        if ask_question(q):
            score += 1
    print("Quiz Finished! Your final score:", score, "/", len(questions))

if __name__ == "__main__":
    main()
