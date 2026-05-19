using UnityEngine;

public class SimpleFPS : MonoBehaviour
{
    public float speed = 3f;
    public float mouseSpeed = 2f;
    float rotX = 0;

    [HideInInspector] public bool aiControlled = false;

    void Update()
    {
        if (aiControlled) return;

        float h = Input.GetAxis("Horizontal");
        float v = Input.GetAxis("Vertical");
        Vector3 move = transform.right * h + transform.forward * v;
        GetComponent<CharacterController>().Move(move * speed * Time.deltaTime);
        float mouseX = Input.GetAxis("Mouse X") * 100 * mouseSpeed * Time.deltaTime;
        float mouseY = Input.GetAxis("Mouse Y") * 100 * mouseSpeed * Time.deltaTime;
        rotX -= mouseY;
        rotX = Mathf.Clamp(rotX, -80, 80);
        Camera.main.transform.localRotation = Quaternion.Euler(rotX, 0, 0);
        transform.Rotate(Vector3.up * mouseX);
    }
}