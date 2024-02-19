import stuff

fn take_pictures{
    initialize camera;
    take the pictures;
    save picture to location;
    ndvi(location of picture);
}

fn ndvi(location) {
    load file (location);
    shift wavelength by specific amount;
    save picture as a copy;
}

fn loop_pictures{
    let number of times = userinput;
    for i=0 until i => number of times i++
        take_pictures;
        wait for specific time;
    print!("pictures complete");
}

fn calculate_speed(distance, time){
    speed = distance / time;
    print!(speed);
}

fn main(){
    start timer;

    calculate_speed;

    while timer > 5 minutes {
        loop_pictures;
    }

    print!("Finished");
}
