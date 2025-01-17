import c4d

def main():
    doc = c4d.documents.GetActiveDocument()
    selected_objects = doc.GetActiveObjects(c4d.GETACTIVEOBJECTFLAGS_0)
    
    # Check if "对象收集" already exists
    collection_object = doc.SearchObject("对象收集")
    
    if not collection_object:
        # Create a new null object
        collection_object = c4d.BaseObject(c4d.Onull)
        collection_object.SetName("对象收集")
        collection_object[c4d.ID_BASEOBJECT_VISIBILITY_EDITOR] = c4d.OBJECT_OFF
        collection_object[c4d.ID_BASEOBJECT_VISIBILITY_RENDER] = c4d.OBJECT_OFF
        doc.InsertObject(collection_object)
    
    # Add selected objects to the collection object
    for obj in selected_objects:
        obj.Remove()
        obj.InsertUnder(collection_object)
    
    c4d.EventAdd()

if __name__ == "__main__":
    main()