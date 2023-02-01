#[macro_use] extern crate rocket;

use std::collections::HashSet;
use std::sync::Arc;
use std::env;
use rocket::serde::{Serialize, Deserialize};
use rocket::fairing::AdHoc;
use rocket::State;

use aws_config::meta::region::RegionProviderChain;
use aws_sdk_s3::Client;

#[derive(Serialize, Deserialize)]
struct Movie {
    title: String,
    year: i32,
    cast: HashSet<String>,
    genres: HashSet<String>,
}

type Movies = Vec<Movie>;

#[derive(Serialize, Deserialize)]
struct SearchResponse {
    items: Movies,
    page: usize,
    page_size: usize,
    has_more: bool
}

#[derive(Clone)]
struct Config {
    db: Arc<Movies>
}

#[get("/?<title_contains>&<year>&<cast>&<genre>&<page>&<page_size>")]
async fn index(
    title_contains: Option<String>,
    year: Option<String>,
    cast: Option<String>,
    genre: Option<String>,
    page: Option<String>,
    page_size: Option<String>,
    state: &State<Config>
) -> String {
    let year_flt = match year {
        Some(year_str) =>
          match year_str.parse::<i32>() {
            Ok(n) => n,
            Err(_e) => 0,
          },
        None => 0
    };
    let title_contains_flt: Option<String> = match title_contains {
        Some(t) => Some(t.to_owned()),
        None => None
    };
    let cast_flt: Option<String> = match cast {
        Some(t) => Some(t.to_owned()),
        None => None
    };
    let genre_flt: Option<String> = match genre {
        Some(t) => Some(t.to_owned()),
        None => None
    };

    let page_val = match page {
        Some(page_str) =>
          match page_str.parse::<usize>() {
            Ok(n) => n,
            Err(_e) => 0,
          },
        None => 0
    };
    let page_size_val = match page_size {
        Some(page_size_str) =>
          match page_size_str.parse::<usize>() {
            Ok(n) => n,
            Err(_e) => 10,
          },
        None => 10
    };

    let mut items: Vec<&Movie> =
        state.db.iter()
           .filter(|movie|
               match &title_contains_flt {
                    Some(t) => (*movie).title.contains(t),
                    None => true
               }
               && (year_flt == 0 || (*movie).year == year_flt)
               && match &cast_flt {
                    Some(t) => (*movie).cast.contains(t),
                    None => true
               }
               && match &genre_flt {
                    Some(t) => (*movie).genres.contains(t),
                    None => true
               }
           )
           .skip(page_size_val * page_val)
           .take(page_size_val + 1)
           .collect();

    let has_more = items.len() > page_size_val;

    if has_more {
        items.pop();
    }

    let items_deref: Movies = items.iter().map(|r| Movie {
        title: (*r).title.clone(),
        year: (*r).year,
        cast: HashSet::new(),
        genres: HashSet::new(),
    }).collect();

    let search_response = SearchResponse {
        items: items_deref,
        page: page_val,
        page_size: page_size_val,
        has_more,
    };

    let res = serde_json::to_string(&search_response);

    res.unwrap()
}


#[launch]
fn rocket() -> _ {
    rocket::build()
        //.manage(db)
        .attach(AdHoc::on_ignite("Manage State", |rocket| async {

            let localstack_service_host: String;
            match env::var("LOCALSTACK_SERVICE_HOST") {
                Ok(val) => {
                    localstack_service_host = val.clone();
                    println!("LOCALSTACK_SERVICE_HOST: {}", val.clone());
                },
                Err(_e) => localstack_service_host = "".to_string(),
            }

            let localstack_service_port: String;
            match env::var("LOCALSTACK_SERVICE_PORT") {
                Ok(val) => {
                    localstack_service_port = val.clone();
                    println!("LOCALSTACK_SERVICE_PORT: {}", val.clone());
                },
                Err(_e) => localstack_service_port = "".to_string(),
            }

            let aws_endpoint_url: String;
            if localstack_service_host.is_empty() {
                match env::var("AWS_ENDPOINT_URL") {
                    Ok(val) => {
                        aws_endpoint_url = val.clone();
                        println!("AWS_ENDPOINT_URL: {}", val.clone());
                    },
                    Err(_e) => aws_endpoint_url = "".to_string(),
                }
            }
            else {
                aws_endpoint_url = format!("http://{}:{}", localstack_service_host, localstack_service_port);
                println!("AWS_ENDPOINT_URL: {}", aws_endpoint_url.clone());
            }

            let aws_storage_bucket_name: String;
            match env::var("AWS_STORAGE_BUCKET_NAME") {
                Ok(val) => {
                    aws_storage_bucket_name = val.clone();
                    println!("AWS_STORAGE_BUCKET_NAME: {}", val.clone());
                },
                Err(_e) => aws_storage_bucket_name = "".to_string(),
            }

            let region_provider = RegionProviderChain::default_provider().or_else("us-east-2");
            let config = aws_config::from_env().region(region_provider).endpoint_url(aws_endpoint_url).load().await;
            let client = Client::new(&config);
            let resp = client.list_objects_v2().bucket(aws_storage_bucket_name.clone()).send().await;

            let mut db: Movies = Vec::new(); // serde_json::from_str(DATA).unwrap();

            match resp {
                Ok(r) => {
                    for object in r.contents().unwrap_or_default() {
                        let key = object.key().unwrap_or_default();
                        println!("{}", key);
                        let data_res = client.get_object().bucket(aws_storage_bucket_name.clone()).key(key).send().await;
                        match data_res {
                            Ok(data) => {
                                let body_res = data.body.collect().await;
                                match body_res {
                                    Ok(body) => {
                                        let json_bytes = body.into_bytes();
                                        let json_str_res= std::str::from_utf8(&json_bytes);
                                        match json_str_res {
                                            Ok(json_str) => {
                                                db = serde_json::from_str(&json_str).unwrap();
                                                println!("Loaded");
                                                break;
                                            },
                                            Err(_e) => println!("Error decoding data")
                                        }

                                    },
                                    Err(_e) => println!("Error reading contents")
                                }
                            },
                            Err(_e) => println!("Error reading data")
                        }
                    }
                },
                Err(_e) => println!("Bucket not found")
            }

            rocket.manage(Config {
                db: Arc::new(db),
            })
        }))
        .mount("/", routes![index])
}
