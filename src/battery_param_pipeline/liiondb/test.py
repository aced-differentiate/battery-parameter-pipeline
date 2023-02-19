import pickle


def function(x):
    return x**2


# pickle function
with open("function.pickle", "wb") as f:
    pickle.dump(function, f)

# unpickle function
with open("function.pickle", "rb") as f:
    function2 = pickle.load(f)

print(function2(2))
