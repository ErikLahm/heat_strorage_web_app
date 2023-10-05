import numpy as np
import plotly.express as px


def main():
    data = [[1, 25, 30, 50, 1], [20, 1, 60, 80, 30], [30, 60, 1, 5, 20]]
    data_array = np.array(data)
    data3d = data_array.reshape((5, 1, 3))
    fig = px.imshow(
        data3d,
        animation_frame=2,
    )

    fig.update_xaxes(side="top")
    fig.show()


if __name__ == "__main__":
    main()
