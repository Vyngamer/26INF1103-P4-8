'''
Common function to print out a centred title
'''

#Prints out a centred title bar
def print_title(title, length=50):
    start = (length//2) - (len(title)//2) #Finds where to start title text in order to center it
    print("\n" + "="*length)
    print(" "*start + title)
    print("="*length)