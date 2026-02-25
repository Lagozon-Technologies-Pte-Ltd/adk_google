print("Testing the application setup...")

list1= [1, 2, 3]
tuple2 = (4, 5, 6) #tuples always start with ()

print("List", list1)
print("Initial tuple", tuple2)

t1 = list(tuple2) #datatype conversion from tuple to list

print(t1)

t1.append(7) #appending 7 to the list t1

tuple2 = tuple(t1) #converting list t1 back to tuple

print("Updated Tuple", tuple2)