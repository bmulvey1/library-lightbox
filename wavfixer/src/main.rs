use std::env;
use std::error::Error;
use std::fs;
use std::process;

fn main() {
    let args: Vec<String> = env::args().collect();

    let config: Config = Config::build(&args).unwrap_or_else(|err| {
        eprintln!("Problem parsing arguments: {err}");
        process::exit(1);
    });

    if let Err(e) = run(config) {
        eprintln!("Application error: {e}");
        process::exit(1);
    }
}

fn run(config: Config) -> Result<(), Box<dyn Error>> {
    let path: String = config.file_path;
    let mut contents: Vec<u8> = fs::read(path.clone())?;
    let first_four: &[u8] = &contents[0..4];
    let third_four: &[u8] = &contents[8..12];
    let riff_id: [u8; 4] = [0x52, 0x49, 0x46, 0x46];
    let wav_id: [u8; 4] = [0x57, 0x41, 0x56, 0x45];

    if (first_four != riff_id) | (third_four != wav_id) {
        return Err("File is not a WAV file")?;
    }

    // format chunk lives at bytes 12-35
    let format_chunk: &[u8] = &contents[12..36];

    if format_chunk[0..4] != [0x66, 0x6D, 0x74, 0x20] {
        return Err("WAV file has unexpected format")?;
    }

    // this should probably return multiple errors at once rather than failing one test at a time

    if format_chunk[10..12] != [0x01, 0x00] {
        return Err(format!(
            "WAV file has wrong channel count (was {}, should be 1)",
            u16::from_le_bytes(format_chunk[10..12].try_into().unwrap())
        ))?;
    }

    if format_chunk[12..16] != [0x80, 0x3e, 0x00, 0x00] {
        return Err(format!(
            "WAV file has wrong sample rate (was {} Hz, should be 16000 Hz)",
            u32::from_le_bytes(format_chunk[12..16].try_into().unwrap())
        ))?;
    }

    if format_chunk[22..24] != [0x10, 0x00] {
        return Err(format!(
            "WAV file has wrong bits per sample setting (was {} bits per sample, should be 16 bits per sample)",
            u16::from_le_bytes(format_chunk[22..24].try_into().unwrap())
        ))?;
    }

    println!("WAV file has correct format");

    let mut current_location: usize = 36;
    let mut found_data: bool = false;
    while !found_data {
        if &contents[current_location..current_location + 4] == [0x64, 0x61, 0x74, 0x61] {
            found_data = true;
        } else {
            let chunk_size: usize = u32::from_le_bytes(
                contents[current_location + 4..current_location + 8]
                    .try_into()
                    .unwrap(),
            ) as usize;
            current_location = current_location + chunk_size + 8;
        }
    }

    println!("found data chunk at 0x{current_location:x}");

    let data_chunk_size: usize = u32::from_le_bytes(
        contents[current_location + 4..current_location + 8]
            .try_into()
            .unwrap(),
    ) as usize;

    println!(
        "data chunk has size 0x{data_chunk_size:x} (last byte of chunk at 0x{:x})",
        current_location + 8 + data_chunk_size
    );

    // let first_sample: &[u8] = &contents[current_location + 8..current_location + 10];
    // println!("first sample: {:x?}", first_sample);
    // let last_sample: &[u8] = &contents
    //     [current_location + 8 + data_chunk_size - 2..current_location + 10 + data_chunk_size - 2];
    // println!("last sample: {:x?}", last_sample);

    // set new first/last sample
    contents.splice(current_location + 8..current_location + 10, [0x80, 0x00]);
    contents.splice(
        current_location + 8 + data_chunk_size - 2..current_location + 10 + data_chunk_size - 2,
        [0x80, 0x00],
    );

    // let new_first_sample: &[u8] = &contents[current_location + 8..current_location + 10];
    // println!("new first sample: {:x?}", new_first_sample);
    // let new_last_sample: &[u8] = &contents
    //     [current_location + 8 + data_chunk_size - 2..current_location + 10 + data_chunk_size - 2];
    // println!("new last sample: {:x?}", new_last_sample);

    let split_path: Vec<_> = path.split(".wav").collect();
    let new_path = format!("{}_new.wav", split_path[0]);
    println!("Path to new WAV file: {new_path}");

    fs::write(new_path, contents)?;

    Ok(())
}

pub struct Config {
    pub file_path: String,
}

impl Config {
    fn build(args: &[String]) -> Result<Config, &'static str> {
        if args.len() < 2 {
            return Err("not enough arguments");
        }
        let file_path: String = args[1].clone();

        Ok(Config { file_path })
    }
}
