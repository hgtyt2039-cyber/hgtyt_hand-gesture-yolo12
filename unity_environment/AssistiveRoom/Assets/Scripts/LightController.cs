using UnityEngine;

public class LightController : MonoBehaviour
{
    public Light myLight;
    bool isOn = true;

    void Update()
    {
        if (Input.GetKeyDown(KeyCode.L))
            Toggle();
    }

    public void Toggle()
    {
        if (myLight == null) return;

        isOn = !isOn;
        myLight.enabled = isOn;
    }

    public void SetLight(bool state)
    {
        if (myLight == null) return;

        isOn = state;
        myLight.enabled = isOn;
    }
}
