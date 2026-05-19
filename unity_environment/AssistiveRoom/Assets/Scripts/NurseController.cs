using UnityEngine;

public class NurseController : MonoBehaviour
{
    public Transform appearPoint;
    public Transform targetPoint;
    public GameObject nurseModel;

    public float moveSpeed = 1.5f;

    bool isActive = false;

    void Start()
    {
        HideNurse();
    }

    void Update()
    {
        // test bằng phím N
        if (Input.GetKeyDown(KeyCode.N))
        {
            if (!isActive)
                ShowNurse();
            else
                HideNurse();
        }

        if (isActive && targetPoint != null)
        {
            transform.position = Vector3.MoveTowards(
                transform.position,
                targetPoint.position,
                moveSpeed * Time.deltaTime
            );
        }
    }

    public void ShowNurse()
    {
        isActive = true;
        nurseModel.SetActive(true);
        transform.position = appearPoint.position;
        transform.rotation = appearPoint.rotation;
    }

    public void HideNurse()
    {
        isActive = false;
        nurseModel.SetActive(false);
    }
}
