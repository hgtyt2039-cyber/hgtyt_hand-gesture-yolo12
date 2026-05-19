using UnityEngine;

public class DoorController : MonoBehaviour
{
    public bool isOpen = false;
    public float openAngle = 90f;
    public float speed = 2f;

    Quaternion closedRot;
    Quaternion openRot;

    void Start()
    {
        closedRot = transform.rotation;
        openRot = Quaternion.Euler(0, openAngle, 0) * closedRot;
    }

    void Update()
    {
        if (isOpen)
            transform.rotation = Quaternion.Slerp(transform.rotation, openRot, Time.deltaTime * speed);
        else
            transform.rotation = Quaternion.Slerp(transform.rotation, closedRot, Time.deltaTime * speed);

        // test tay
        if (Input.GetKeyDown(KeyCode.O)) OpenDoor();
        if (Input.GetKeyDown(KeyCode.C)) CloseDoor();
    }

    // 👉 cho CommandServer gọi
    public void OpenDoor() { isOpen = true; }
    public void CloseDoor() { isOpen = false; }
}
