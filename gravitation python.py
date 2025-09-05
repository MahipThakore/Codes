#value of universal gravitation constant and some extra constants
G = 6.67/10**-11
Me = 5.9*(10**24)
Re = 6371*10**3
g = 9.8
#greetings
print("hello user")
print("this program can calculate the following variables using given values by the user")
#defining choices
print("1.Gravitational Force between two masses")
print("2.Gravitational Force of Earth applied to a object above a height from the Earth's surface")
print("3.Gravitational Force of Earth applied to a object below a height from the Earth's surface")
print("4.Intensity of Gravitational Field of a given object with mass")
print("5.Gravitational Potential of the given object with mass")
print("6.Potential Energy of a Gravitational field")
print("7.The Escape Velocity of any planet provided the radius and mass of the planet")
print("8.orbital velocity of a satellite")
#taking input for functioning from user
choice = int(input("Enter your choice : "))
#using if elif else to compute the result for the user based on the request
#m denotes mass,r denotes distance or radius,number after them denotes the choice no.
if choice == 1 :
    M1 = float(input('mass of object 1 : '))
    m1 = float(input('mass of object 2 : '))
    r1 = float(input('distance between both objects : '))
    print('The Force between m1 and m2 is',(G*M1*m1)/r1**2,"N")
elif choice == 2 :
    h2 = float(input("height of object from surface of Earth : "))
    print("The applied force of Earth's gravity at the given height is",g/(1+(h2/Re))**2,"m/s*2")
elif choice == 3 :
    h3 = float(input("Depth of object from surface of Earth : "))
    print("The applied force of Earth's gravity at the given Depth is",g(1-(h3/Re)),"m/s**2")
elif choice == 4 :
    M4 = float(input('mass of object : '))
    r4 = float(input('distance from centre of the object : '))
    print("Intensity of Gravitational Field of the given object is",(G*M4)/(r4*r4),"N/kg")
elif choice == 5 :
    work_done = float(input('Work done on object : '))
    M5 = float(input('mass of object : '))
    print("Gravitational Potential of the given object is",-(work_done)/M5,"J/Kg")
elif choice == 6 :
    M6 = float(input('mass of object 1 : '))
    m6 = float(input('mass of object 2 : '))
    r6 = float(input('distance between both objects : '))
    print('The Potential Energy of the Gravitational field is',(G*M6*m6)/r6)
elif choice == 7 : 
    mp = float(input('mass of planet : '))
    rp = float(input('radius of planet : '))
    print('The Escape Velocity of the planet is',((G*2*mp)/rp)**(0.5))
elif choice == 8 : 
    m7 = float(input('mass of planet : '))
    r7 = float(input('radius of planet : '))
    print('The orbital Velocity of the satellite is',((G*m7)/r7)**(0.5))
else :
    print("invalid choice")