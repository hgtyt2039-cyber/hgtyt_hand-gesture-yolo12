using UnityEngine;

public class BedController : MonoBehaviour
{
    public Transform pivot;
    public float maxAngle = 45f;
    public float speed = 2f;

    bool isRaised = false;
    Quaternion lyingRotation;
    Quaternion raisedRotation;

    void Start()
    {
        lyingRotation = pivot.localRotation;
        raisedRotation = Quaternion.Euler(-maxAngle, 0, 0) * lyingRotation;
    }

    void Update()
    {
        if (Input.GetKeyDown(KeyCode.B))
            Toggle();

        Quaternion target = isRaised ? raisedRotation : lyingRotation;
        pivot.localRotation = Quaternion.Slerp(pivot.localRotation, target, Time.deltaTime * speed);
    }

    public void Toggle() { isRaised = !isRaised; }
    public void ResetBed() { isRaised = false; }
}
