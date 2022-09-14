import face_recognition
import os
import pickle
import time

path="students"
images=os.listdir(path)
encoding=[]
names=[]
id=21060900
ids=[]

print("MODEL TRAINING STARTED......")
q=time.time()

for folder in images:
    for image in os.listdir(f"{path}/{folder}"):
        if str(folder) not in names:
            face=face_recognition.load_image_file(f"{path}/{folder}/{image}")
            try:
                loc=face_recognition.face_locations(face)
                end=face_recognition.face_encodings(face,loc,model="small")[0]
                encoding.append(end)
                names.append(str(folder))
                ids.append(id+os.listdir(path).index(folder)+1)
            except:
                continue

with open("record/encodings.txt","wb") as f:
    pickle.dump(encoding,f)
with open("record/names.txt","wb") as f:
    pickle.dump(names,f)
with open("record/ids.txt","wb") as f:
    pickle.dump(ids,f)

print("MODEL TRAINING COMPLETED in",round(time.time()-q,2),"seconds")