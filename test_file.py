def some_python_function():
    

    print("This is a test function.")

def another_function():
    return 42

#TODO: do a thing
#FIXME: make it better
msg = "TODO: abc"

x=0;
print("debug: value x =", x)
# print("commented")
msg = "print(string)"


try:
    x = 1 / 0
except:                         # detected H009
    pass

try:
    y = int("abc")
except ValueError:              # not detected (type provided)
    pass

# except:                       # not detected



MAX_TIMEOUT = 30                # not detected - constant

response_code = 0
if response_code == 404:        # detected H010
    pass

delay = 0.5 * 1000              # detected H010 (1000)

if x == 0 or y == 1:            # not detected — 0 and 0 allowed
    pass

#  42                           # not detected
msg = "kod błędu: 404"          # not detected